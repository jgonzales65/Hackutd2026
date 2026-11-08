"""Bounded BCAD ingestion. No database connection unless explicitly requested."""
import argparse
import json
import logging
import math
import os
from pathlib import Path
import time

import requests
from dotenv import load_dotenv
from shapely.geometry import shape
from shapely.validation import explain_validity

ENDPOINT = 'https://services.arcgis.com/g1fRTDLeMgspWrYp/ArcGIS/rest/services/BCAD_Parcels/FeatureServer/0/query'
LOG = logging.getLogger('bcad')
INSERT_SQL = """
INSERT INTO public.parcels (parcel_id, formatted_address, geom, land_value, zoning_code)
VALUES (%s, %s, public.ST_SetSRID(public.ST_GeomFromGeoJSON(%s), 4326), NULL, NULL)
ON CONFLICT (parcel_id) DO NOTHING RETURNING parcel_id
"""


class ImportFailure(Exception):
    pass


def normalize_geometry(geometry):
    if not isinstance(geometry, dict) or geometry.get('type') not in ('Polygon', 'MultiPolygon'):
        raise ValueError('missing or unsupported geometry type')
    if 'crs' in geometry:
        validate_crs(geometry)
    coordinates = geometry.get('coordinates')
    polygons = [coordinates] if geometry['type'] == 'Polygon' else coordinates
    if not isinstance(polygons, list) or not polygons:
        raise ValueError('empty or malformed polygons')
    for polygon in polygons:
        if not isinstance(polygon, list) or not polygon:
            raise ValueError('empty or malformed polygon')
        for ring in polygon:
            if not isinstance(ring, list) or len(ring) < 4 or ring[0] != ring[-1]:
                raise ValueError('rings must have at least four positions and be closed')
            for point in ring:
                if not isinstance(point, list) or len(point) != 2:
                    raise ValueError('expected two-dimensional longitude/latitude')
                if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in point):
                    raise ValueError('non-finite or non-numeric coordinate')
                if not (-180 <= point[0] <= 180 and -90 <= point[1] <= 90):
                    raise ValueError('coordinates outside SRID 4326 bounds')
    result = {'type': 'MultiPolygon', 'coordinates': polygons}
    geom = shape(result)
    if geom.is_empty or not geom.is_valid or geom.area <= 0:
        raise ValueError('invalid geometry: ' + explain_validity(geom))
    return result


def validate_crs(document):
    # GeoJSON without a CRS uses longitude/latitude; the query also requests 4326.
    crs = document.get('crs')
    if crs is None:
        return
    name = crs.get('properties', {}).get('name') if isinstance(crs, dict) else None
    if name not in ('EPSG:4326', 'urn:ogc:def:crs:EPSG::4326', 'urn:ogc:def:crs:OGC:1.3:CRS84'):
        raise ImportFailure('API returned an unexpected coordinate reference system')


def normalize_feature(feature):
    if not isinstance(feature, dict) or feature.get('type') != 'Feature':
        raise ValueError('not a GeoJSON Feature')
    props = feature.get('properties')
    if not isinstance(props, dict):
        raise ValueError('missing properties')
    prop_id = props.get('PropID')
    if isinstance(prop_id, bool) or not isinstance(prop_id, (str, int)):
        raise ValueError('missing or invalid PropID')
    parcel_id = str(prop_id).strip()
    if not parcel_id.isascii() or not parcel_id.isdigit() or int(parcel_id) <= 0:
        raise ValueError('PropID must be a positive integer')
    address = props.get('Situs')
    if not isinstance(address, str) or not address.strip() or address.strip().lower() in ('null', 'none', 'n/a', 'unknown'):
        raise ValueError('missing or invalid Situs address')
    return {'parcel_id': str(int(parcel_id)), 'formatted_address': address.strip(),
            'geom': normalize_geometry(feature.get('geometry'))}


def fetch_page(session, after, count, retries=3):
    params = {'where': f'PropID > 0 AND OBJECTID > {after}',
              'outFields': 'OBJECTID,PropID,Geo_id,Situs', 'returnGeometry': 'true',
              'outSR': 4326, 'f': 'geojson', 'orderByFields': 'OBJECTID ASC',
              'resultRecordCount': count}
    for attempt in range(retries + 1):
        try:
            response = session.get(ENDPOINT, params=params, timeout=(10, 60))
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise ImportFailure('API response is not an object')
            if 'error' in data:
                # Do not log arbitrary server messages or response bodies.
                raise ImportFailure('ArcGIS returned an error')
            if data.get('type') != 'FeatureCollection' or not isinstance(data.get('features'), list):
                raise ImportFailure('API response is not a FeatureCollection')
            validate_crs(data)
            return data['features']
        except (requests.RequestException, ValueError, ImportFailure):
            if attempt == retries:
                raise ImportFailure('BCAD request failed after retries; checkpoint unchanged') from None
            LOG.warning('BCAD request failed; retry %d/%d', attempt + 1, retries)
            time.sleep(min(2 ** attempt, 30))


def page_cursor(features, after):
    cursor = after
    for feature in features:
        props = feature.get('properties') if isinstance(feature, dict) else None
        oid = props.get('OBJECTID') if isinstance(props, dict) else None
        if isinstance(oid, bool) or not isinstance(oid, int) or oid <= cursor:
            raise ImportFailure('missing or unordered OBJECTID; checkpoint unchanged')
        cursor = oid
    return cursor


def write_batch(conn, records):
    inserted = 0
    # Commit the entire page before advancing its checkpoint.
    with conn.transaction():
        with conn.cursor() as cur:
            for record in records:
                cur.execute(INSERT_SQL, (record['parcel_id'], record['formatted_address'], json.dumps(record['geom'], allow_nan=False)))
                inserted += cur.fetchone() is not None
    return inserted


def preflight(conn):
    """Read only: inspect actual schema, role and policies before any writes."""
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute('SET TRANSACTION READ ONLY')
            cur.execute("SELECT current_user, c.relrowsecurity, c.relforcerowsecurity FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relname='parcels'")
            row = cur.fetchone()
            if not row or row[0] in ('anon', 'authenticated', 'authenticator'):
                raise ImportFailure('parcels missing or browser-facing database role selected')
            LOG.info('Database preflight: RLS enabled=%s forced=%s', row[1], row[2])
            cur.execute("SELECT column_name, is_nullable, column_default FROM information_schema.columns WHERE table_schema='public' AND table_name='parcels'")
            columns = {r[0]: r[1:] for r in cur.fetchall()}
            if not {'id', 'parcel_id', 'formatted_address', 'land_value', 'zoning_code', 'geom', 'created_at'} <= columns.keys():
                raise ImportFailure('parcels schema differs from expected columns')
            if columns['land_value'][0] != 'YES' or columns['zoning_code'][0] != 'YES':
                raise ImportFailure('unverified value columns must allow null')
            cur.execute("SELECT type, srid, coord_dimension FROM public.geometry_columns WHERE f_table_schema='public' AND f_table_name='parcels' AND f_geometry_column='geom'")
            if cur.fetchone() != ('MULTIPOLYGON', 4326, 2):
                raise ImportFailure('expected public.parcels.geom MULTIPOLYGON(4326), dimension 2')
            cur.execute("SELECT indexdef FROM pg_indexes WHERE schemaname='public' AND tablename='parcels'")
            indexes = [r[0] for r in cur.fetchall()]
            if not any('UNIQUE INDEX' in s and '(parcel_id)' in s and ' WHERE ' not in s for s in indexes):
                raise ImportFailure('expected non-partial unique parcel_id index')
            cur.execute("SELECT policyname, cmd, roles, qual, with_check FROM pg_policies WHERE schemaname='public' AND tablename='parcels'")
            for policy in cur.fetchall():
                LOG.info('Existing parcels policy: name=%s command=%s roles=%s', *policy[:3])
            cur.execute("SELECT has_table_privilege(current_user, 'public.parcels', 'INSERT'), has_table_privilege(current_user, 'public.parcels', 'SELECT')")
            if cur.fetchone() != (True, True):
                raise ImportFailure('database role requires INSERT and SELECT on parcels')
    LOG.info('Read-only preflight passed; policies and schema were not changed')


def load_checkpoint(path, mode):
    if not path.exists():
        return 0
    data = json.loads(path.read_text())
    if data.get('endpoint') != ENDPOINT or data.get('mode') != mode or data.get('version') != 1:
        raise ImportFailure('checkpoint belongs to a different source or mode')
    after = data.get('after')
    if isinstance(after, bool) or not isinstance(after, int) or after < 0:
        raise ImportFailure('invalid checkpoint cursor')
    return after


def save_checkpoint(path, mode, after):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps({'version': 1, 'endpoint': ENDPOINT, 'mode': mode, 'after': after}))
    temp.replace(path)


def run(session, *, batch_size, limit, checkpoint, mode, conn=None, resume=False):
    if checkpoint.exists() and not resume:
        raise ImportFailure('checkpoint exists; use --resume or choose a new --checkpoint')
    after = load_checkpoint(checkpoint, mode) if resume else 0
    scanned = valid = skipped = inserted = duplicates = 0
    while limit is None or scanned < limit:
        count = batch_size if limit is None else min(batch_size, limit - scanned)
        features = fetch_page(session, after, count)
        if not features:
            break
        if len(features) > count:
            raise ImportFailure('API exceeded requested page size')
        next_after = page_cursor(features, after)
        records, seen = [], set()
        for feature in features:
            try:
                record = normalize_feature(feature)
            except (ValueError, ImportFailure) as exc:
                skipped += 1
                LOG.warning('Skip OBJECTID=%s: %s', feature['properties']['OBJECTID'], exc)
                continue
            if record['parcel_id'] in seen:
                duplicates += 1
                continue
            seen.add(record['parcel_id'])
            records.append(record)
        page_inserted = write_batch(conn, records) if conn is not None else 0
        save_checkpoint(checkpoint, mode, next_after)
        after = next_after
        scanned += len(features)
        valid += len(records)
        inserted += page_inserted
        if conn is not None:
            duplicates += len(records) - page_inserted
        LOG.info('scanned=%d valid=%d skipped=%d duplicates=%d inserted=%d last_OBJECTID=%d', scanned, valid, skipped, duplicates, inserted, after)
    return {'scanned': scanned, 'valid': valid, 'skipped': skipped, 'duplicates': duplicates, 'inserted': inserted}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--dry-run', action='store_true', help='default; no database connection')
    action.add_argument('--write', action='store_true', help='write only after explicit team approval')
    action.add_argument('--preflight', action='store_true', help='read-only database inspection; no BCAD download')
    parser.add_argument('--batch-size', type=int, default=100)
    parser.add_argument('--limit', type=int, default=100, help='maximum source features examined per invocation, including invalid records')
    parser.add_argument('--full-county', action='store_true', help='remove total limit; requires explicit team approval')
    parser.add_argument('--checkpoint', type=Path)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 1000 or args.limit <= 0:
        parser.error('batch size must be 1..1000; limit must be positive')
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    mode = 'write' if args.write else 'dry-run'
    checkpoint = args.checkpoint or Path(__file__).parent / '.state' / (mode + '.json')
    conn = None
    try:
        if args.write or args.preflight:
            import psycopg
            load_dotenv(Path(__file__).parent / '.env')
            url = os.getenv('SUPABASE_DB_URL')
            if not url:
                raise ImportFailure('SUPABASE_DB_URL is required for database access')
            conn = psycopg.connect(url, sslmode='require', connect_timeout=15, autocommit=True)
            preflight(conn)
        if not args.preflight:
            with requests.Session() as session:
                result = run(session, batch_size=args.batch_size, limit=None if args.full_county else args.limit,
                             checkpoint=checkpoint, mode=mode, conn=conn, resume=args.resume)
                LOG.info('Completed %s: %s', mode, result)
        return 0
    except Exception as exc:
        # Driver errors may include connection details. Never print their text.
        LOG.error('%s', str(exc) if isinstance(exc, ImportFailure) else 'Operation failed (' + type(exc).__name__ + '); checkpoint retained for replay')
        return 1
    finally:
        if conn is not None:
            conn.close()


if __name__ == '__main__':
    raise SystemExit(main())
