import copy
import tempfile
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

import requests
from backend.ingestion import import_parcels as importer

RING = [[-98.5, 29.4], [-98.4, 29.4], [-98.4, 29.5], [-98.5, 29.5], [-98.5, 29.4]]


def feature(oid=1, pid=123):
    return {'type': 'Feature', 'properties': {'OBJECTID': oid, 'PropID': pid, 'Situs': '123 MAIN ST'},
            'geometry': {'type': 'Polygon', 'coordinates': [copy.deepcopy(RING)]}}


class GeometryTests(unittest.TestCase):
    def test_polygon_and_hole_preserved(self):
        hole = [[-98.48, 29.42], [-98.48, 29.44], [-98.46, 29.44], [-98.46, 29.42], [-98.48, 29.42]]
        geometry = {'type': 'Polygon', 'coordinates': [RING, hole]}
        result = importer.normalize_geometry(geometry)
        self.assertEqual(result, {'type': 'MultiPolygon', 'coordinates': [[RING, hole]]})
        self.assertEqual(importer.normalize_geometry(result), result)

    def test_invalid_geometries(self):
        cases = [None, {'type': 'Point', 'coordinates': [0, 0]},
                 {'type': 'Polygon', 'coordinates': []},
                 {'type': 'Polygon', 'coordinates': [RING[:-1]]},
                 {'type': 'Polygon', 'coordinates': [[[0, 0], [1, 1], [1, 0], [0, 1], [0, 0]]]},
                 {'type': 'Polygon', 'coordinates': [[[181, 0]] * 4]},
                 {'type': 'Polygon', 'coordinates': [[[float('nan'), 0]] * 4]},
                 {'type': 'Polygon', 'coordinates': [[[0, 0, 1]] * 4]}]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(ValueError):
                importer.normalize_geometry(case)

    def test_crs(self):
        with self.assertRaises(importer.ImportFailure):
            importer.validate_crs({'crs': {'properties': {'name': 'EPSG:3857'}}})

    def test_invalid_fields(self):
        for key, value in [('PropID', None), ('PropID', 0), ('PropID', True), ('PropID', 1.5),
                           ('PropID', 'nan'), ('Situs', ''), ('Situs', None), ('Situs', 'unknown')]:
            f = feature()
            f['properties'][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                importer.normalize_feature(f)
        f = feature()
        f['properties']['MailingAddress'] = 'WRONG ADDRESS'
        record = importer.normalize_feature(f)
        self.assertEqual(record['formatted_address'], '123 MAIN ST')
        self.assertNotIn('land_value', record)
        self.assertNotIn('zoning_code', record)


class ApiTests(unittest.TestCase):
    @patch.object(importer.time, 'sleep')
    def test_errors_retry(self, sleep):
        for response in [{'error': {'code': 500}}, [], {'type': 'FeatureCollection', 'features': None}]:
            session = MagicMock()
            session.get.return_value.json.return_value = response
            with self.assertRaises(importer.ImportFailure):
                importer.fetch_page(session, 0, 100, retries=1)
            self.assertEqual(session.get.call_count, 2)

    @patch.object(importer.time, 'sleep')
    def test_http_error_and_recovery(self, sleep):
        session = MagicMock()
        good = MagicMock()
        good.json.return_value = {'type': 'FeatureCollection', 'features': []}
        session.get.side_effect = [requests.Timeout(), good]
        self.assertEqual(importer.fetch_page(session, 9, 3, retries=1), [])
        self.assertEqual(session.get.call_args.kwargs['params']['where'], 'PropID > 0 AND OBJECTID > 9')
        self.assertEqual(session.get.call_args.kwargs['timeout'], (10, 60))
        session.get.side_effect = None
        session.get.return_value.raise_for_status.side_effect = requests.HTTPError()
        with self.assertRaises(importer.ImportFailure):
            importer.fetch_page(session, 0, 1, retries=0)


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'checkpoint.json'

    @patch.object(importer, 'fetch_page')
    def test_pagination_skips_and_bounded_limit(self, fetch):
        fetch.side_effect = [[feature(2), feature(4, 0)], [feature(7, 456)]]
        result = importer.run(None, batch_size=2, limit=3, checkpoint=self.path, mode='dry-run')
        self.assertEqual(result['scanned'], 3)
        self.assertEqual(result['valid'], 2)
        self.assertEqual(result['skipped'], 1)
        self.assertEqual(fetch.call_args_list[1].args[1:], (4, 1))
        self.assertEqual(importer.load_checkpoint(self.path, 'dry-run'), 7)

    @patch.object(importer, 'fetch_page')
    def test_failure_resume_and_mode_isolation(self, fetch):
        fetch.side_effect = [[feature(10)], importer.ImportFailure('offline')]
        with self.assertRaises(importer.ImportFailure):
            importer.run(None, batch_size=1, limit=2, checkpoint=self.path, mode='dry-run')
        self.assertEqual(importer.load_checkpoint(self.path, 'dry-run'), 10)
        with self.assertRaises(importer.ImportFailure):
            importer.load_checkpoint(self.path, 'write')
        fetch.side_effect = [[feature(20, 789)]]
        importer.run(None, batch_size=1, limit=1, checkpoint=self.path, mode='dry-run', resume=True)
        self.assertEqual(fetch.call_args.args[1], 10)

    @patch.object(importer, 'fetch_page')
    def test_unordered_page_does_not_checkpoint(self, fetch):
        fetch.return_value = [feature(2), feature(1)]
        with self.assertRaises(importer.ImportFailure):
            importer.run(None, batch_size=2, limit=2, checkpoint=self.path, mode='dry-run')
        self.assertFalse(self.path.exists())

    @patch.object(importer, 'write_batch')
    @patch.object(importer, 'fetch_page')
    def test_duplicates_and_db_failure(self, fetch, write):
        fetch.return_value = [feature(1), feature(2)]
        write.return_value = 0  # Existing database parcel: ON CONFLICT returns no row.
        result = importer.run(None, batch_size=2, limit=2, checkpoint=self.path, mode='write', conn=object())
        self.assertEqual(len(write.call_args.args[1]), 1)
        self.assertEqual(result['duplicates'], 2)
        write.side_effect = RuntimeError('database failed')
        fetch.return_value = [feature(3, 999)]
        with self.assertRaises(RuntimeError):
            importer.run(None, batch_size=1, limit=1, checkpoint=self.path, mode='write', conn=object(), resume=True)
        self.assertEqual(importer.load_checkpoint(self.path, 'write'), 2)

    def test_parameterized_conflict_insert(self):
        conn = MagicMock()
        cur = conn.cursor.return_value.__enter__.return_value
        cur.fetchone.side_effect = [('123',), None]
        records = [importer.normalize_feature(feature())] * 2
        self.assertEqual(importer.write_batch(conn, records), 1)
        sql, params = cur.execute.call_args.args
        self.assertIn('ON CONFLICT (parcel_id) DO NOTHING', sql)
        self.assertIn('public.ST_GeomFromGeoJSON(%s)', sql)
        self.assertEqual(params[0], '123')
        self.assertEqual(params[1], '123 MAIN ST')


class PreflightTests(unittest.TestCase):
    def test_schema_and_policies_read_only(self):
        conn = MagicMock()
        cur = conn.cursor.return_value.__enter__.return_value
        cur.fetchone.side_effect = [('postgres', True, False), ('MULTIPOLYGON', 4326, 2), (True, True)]
        columns = [(name, 'YES', None) for name in
                   ('id', 'parcel_id', 'formatted_address', 'land_value', 'zoning_code', 'geom', 'created_at')]
        cur.fetchall.side_effect = [columns, [('CREATE UNIQUE INDEX parcels_parcel_id_key ON public.parcels USING btree (parcel_id)',)],
                                   [('read_policy', 'SELECT', ['authenticated'], 'true', None)]]
        importer.preflight(conn)
        statements = [call.args[0] for call in cur.execute.call_args_list]
        self.assertEqual(statements[0], 'SET TRANSACTION READ ONLY')
        self.assertTrue(all(sql.startswith(('SELECT', 'SET TRANSACTION READ ONLY')) for sql in statements))

    def test_browser_role_rejected_before_writes(self):
        conn = MagicMock()
        cur = conn.cursor.return_value.__enter__.return_value
        cur.fetchone.return_value = ('anon', True, False)
        with self.assertRaises(importer.ImportFailure):
            importer.preflight(conn)


if __name__ == '__main__':
    unittest.main()
