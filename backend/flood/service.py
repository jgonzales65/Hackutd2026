"""Real FEMA polygon overlap. No probabilities or loss estimates."""
import os
from pathlib import Path

from dotenv import load_dotenv
import psycopg

SOURCE = 'https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28'


def connect():
    load_dotenv(Path(__file__).resolve().parents[1] / 'ingestion' / '.env')
    url = os.getenv('SUPABASE_DB_URL')
    if not url:
        raise RuntimeError('SUPABASE_DB_URL is required')
    return psycopg.connect(url, sslmode='require', connect_timeout=15)


OVERLAP_SQL = """
SELECT z.object_id, z.flood_zone, z.zone_subtype, z.sfha,
       z.source_citation, z.source_url, z.retrieved_at::text
FROM public.parcels p JOIN public.fema_flood_zones z
  ON public.ST_Intersects(p.geom, z.geom)
WHERE p.parcel_id = %s
ORDER BY z.object_id
"""


def assess_parcel(conn, parcel_id):
    """Read-only; null means unknown, false is reserved for complete assessments."""
    with conn.transaction():
        conn.execute('SET TRANSACTION READ ONLY')
        row = conn.execute('SELECT geom IS NOT NULL AND NOT ST_IsEmpty(geom) AND ST_IsValid(geom) '
                           'FROM public.parcels WHERE parcel_id = %s', (parcel_id,)).fetchone()
        if row is None:
            return None
        base = {'parcel_id': parcel_id, 'mapped_flood_hazard_overlaps': None,
                'special_flood_hazard_area_overlaps': None,
                'fema_zone_classifications': [], 'matches': [], 'source': SOURCE,
                'assessment_status': 'coverage_incomplete', 'coverage_complete': False}
        if not row[0]:
            return {**base, 'assessment_status': 'parcel_geometry_unavailable'}
        if conn.execute("SELECT to_regclass('public.fema_flood_zones')").fetchone()[0] is None:
            return {**base, 'assessment_status': 'hazard_data_unavailable'}
        matches = conn.execute(OVERLAP_SQL, (parcel_id,)).fetchall()
        keys = ('object_id', 'flood_zone', 'zone_subtype', 'sfha', 'source_citation', 'source_url', 'retrieved_at')
        base['matches'] = [dict(zip(keys, m)) for m in matches]
        base['fema_zone_classifications'] = sorted({m[1] for m in matches})
        # X can be shaded (0.2% annual chance) or minimal hazard. Preserve subtype.
        # SFHA is FEMA's explicit flag; do not treat every mapped X polygon as hazard.
        hazard = any(m[3] is True or '0.2 PCT ANNUAL CHANCE' in (m[2] or '').upper() for m in matches)
        if matches:
            base['assessment_status'] = 'overlap_found_partial_coverage'
        if hazard:
            base['mapped_flood_hazard_overlaps'] = True
        if any(m[3] is True for m in matches):
            base['special_flood_hazard_area_overlaps'] = True
        return base
