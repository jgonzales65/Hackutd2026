import os
import unittest
from unittest.mock import MagicMock, patch

from backend.flood import service, ingest


class AssessmentTests(unittest.TestCase):
    def connection(self, matches=(), exists=True, geometry=True, table=True):
        conn = MagicMock()
        conn.execute.return_value.fetchone.side_effect = [
            (geometry,) if exists else None, ('fema_flood_zones' if table else None,)]
        conn.execute.return_value.fetchall.return_value = matches
        return conn

    def test_hazard_overlap_preserves_classification_and_source(self):
        conn = self.connection([(7, 'AE', None, True, 'FEMA citation', service.SOURCE, '2026-11-08')])
        result = service.assess_parcel(conn, '123')
        self.assertTrue(result['mapped_flood_hazard_overlaps'])
        self.assertTrue(result['special_flood_hazard_area_overlaps'])
        self.assertEqual(result['fema_zone_classifications'], ['AE'])
        self.assertEqual(result['matches'][0]['source_citation'], 'FEMA citation')
        self.assertFalse(result['coverage_complete'])

    def test_no_match_is_unknown(self):
        result = service.assess_parcel(self.connection(), '123')
        self.assertIsNone(result['mapped_flood_hazard_overlaps'])
        self.assertEqual(result['assessment_status'], 'coverage_incomplete')

    def test_minimal_hazard_x_does_not_mean_hazard_overlap(self):
        result = service.assess_parcel(self.connection([
            (8, 'X', 'AREA OF MINIMAL FLOOD HAZARD', False, None, service.SOURCE, 'today')]), '123')
        self.assertIsNone(result['mapped_flood_hazard_overlaps'])
        self.assertEqual(result['fema_zone_classifications'], ['X'])

    def test_shaded_x_is_mapped_hazard(self):
        result = service.assess_parcel(self.connection([
            (8, 'X', '0.2 PCT ANNUAL CHANCE FLOOD HAZARD', False, None, service.SOURCE, 'today')]), '123')
        self.assertTrue(result['mapped_flood_hazard_overlaps'])
        self.assertIsNone(result['special_flood_hazard_area_overlaps'])

    def test_missing_parcel_geometry_or_dataset(self):
        self.assertIsNone(service.assess_parcel(self.connection(exists=False), 'missing'))
        for kwargs, status in [({'geometry': False}, 'parcel_geometry_unavailable'),
                               ({'table': False}, 'hazard_data_unavailable')]:
            self.assertEqual(service.assess_parcel(self.connection(**kwargs), '123')['assessment_status'], status)

    def test_api_error_does_not_expose_secrets(self):
        from backend.flood.api import flood_risk
        from fastapi import HTTPException
        with patch('backend.flood.api.connect', side_effect=RuntimeError('secret-password')):
            with self.assertRaises(HTTPException) as ctx:
                flood_risk('123')
        self.assertEqual(ctx.exception.status_code, 503)
        self.assertNotIn('secret', ctx.exception.detail)

    def test_arcgis_error_and_bound_rejected(self):
        conn = MagicMock()
        conn.execute.return_value.fetchone.return_value = (-98.55, 29.38, -98.44, 29.47)
        with patch.object(ingest.requests, 'get') as get:
            get.return_value.json.return_value = {'error': {'code': 500}}
            with self.assertRaises(ValueError):
                ingest.download(conn, 100)
            with self.assertRaises(ValueError):
                ingest.download(conn, 201)


@unittest.skipUnless(os.getenv('RUN_FLOOD_DB_TESTS') == '1', 'Opt-in live read-only PostGIS tests')
class PostGISTests(unittest.TestCase):
    def test_intersection_boundary_disjoint_and_hole(self):
        with service.connect() as conn:
            conn.execute('SET TRANSACTION READ ONLY')
            result = conn.execute("""WITH p AS (
                SELECT ST_GeomFromText('POLYGON((0 0,2 0,2 2,0 2,0 0))',4326) g)
                SELECT ST_Intersects(g, ST_GeomFromText('POLYGON((1 1,3 1,3 3,1 3,1 1))',4326)),
                       ST_Intersects(g, ST_GeomFromText('POLYGON((2 0,3 0,3 1,2 1,2 0))',4326)),
                       ST_Intersects(g, ST_GeomFromText('POLYGON((3 3,4 3,4 4,3 4,3 3))',4326)),
                       ST_Intersects(ST_Point(1,1,4326), ST_GeomFromText(
                         'POLYGON((0 0,2 0,2 2,0 2,0 0),(0.5 0.5,0.5 1.5,1.5 1.5,1.5 0.5,0.5 0.5))',4326))
                FROM p""").fetchone()
            self.assertEqual(result, (True, True, False, False))

    def test_real_imported_parcel_overlap(self):
        with service.connect() as conn:
            conn.execute('SET TRANSACTION READ ONLY')
            row = conn.execute('''SELECT p.parcel_id FROM public.parcels p
                JOIN public.fema_flood_zones z ON ST_Intersects(p.geom,z.geom)
                WHERE z.sfha IS TRUE LIMIT 1''').fetchone()
            conn.commit()
            self.assertIsNotNone(row, 'Pilot must contain a real SFHA parcel overlap')
            result = service.assess_parcel(conn, row[0])
            self.assertTrue(result['mapped_flood_hazard_overlaps'])
            self.assertTrue(result['matches'])


if __name__ == '__main__':
    unittest.main()
