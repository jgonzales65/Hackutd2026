"""Bounded FEMA pilot; download first, write only with --write."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import requests
from backend.flood.service import SOURCE, connect
from backend.ingestion.import_parcels import normalize_geometry, validate_crs

DATA = Path(__file__).resolve().parents[1] / 'ingestion' / 'data' / 'fema-pilot.json'


def parcel_fingerprint(conn):
    return conn.execute("SELECT count(*), md5(string_agg(md5(row_to_json(p)::text), '' ORDER BY parcel_id)) "
                        "FROM public.parcels p").fetchone()


def download(conn, limit=100):
    if not 1 <= limit <= 200:
        raise ValueError('Pilot limit must be 1..200')
    with conn.transaction():
        conn.execute('SET TRANSACTION READ ONLY')
        bbox = conn.execute('SELECT ST_XMin(e), ST_YMin(e), ST_XMax(e), ST_YMax(e) '
                            'FROM (SELECT ST_Extent(geom)::box3d e FROM public.parcels) s').fetchone()
    if bbox is None or any(x is None for x in bbox):
        raise ValueError('No parcel bounds available')
    response = requests.get(SOURCE + '/query', params={
        'f': 'geojson', 'where': '1=1', 'geometry': ','.join(map(str, bbox)),
        'geometryType': 'esriGeometryEnvelope', 'inSR': 4326, 'outSR': 4326,
        'spatialRel': 'esriSpatialRelIntersects', 'returnGeometry': 'true',
        'outFields': 'OBJECTID,FLD_ZONE,ZONE_SUBTY,SFHA_TF,SOURCE_CIT',
        'orderByFields': 'OBJECTID ASC', 'resultRecordCount': limit,
    }, timeout=(10, 90))
    response.raise_for_status()
    data = response.json()
    if data.get('error') or data.get('type') != 'FeatureCollection' or not isinstance(data.get('features'), list):
        raise ValueError('FEMA service returned an error or invalid GeoJSON')
    validate_crs(data)
    if len(data['features']) > limit:
        raise ValueError('FEMA exceeded bounded pilot limit')
    records, skipped = [], []
    for feature in data['features']:
        props = feature.get('properties', {})
        try:
            oid = props['OBJECTID']
            if isinstance(oid, bool) or not isinstance(oid, int) or not props.get('FLD_ZONE'):
                raise ValueError('Missing FEMA object ID or zone')
            flag = props.get('SFHA_TF')
            records.append({'object_id': oid, 'flood_zone': props['FLD_ZONE'],
                            'zone_subtype': props.get('ZONE_SUBTY'),
                            'sfha': True if flag == 'T' else False if flag == 'F' else None,
                            'source_citation': props.get('SOURCE_CIT'),
                            'geometry': normalize_geometry(feature.get('geometry'))})
        except (ValueError, KeyError) as exc:
            skipped.append({'object_id': props.get('OBJECTID'), 'reason': str(exc)})
    return {'source': SOURCE, 'retrieved_at': datetime.now(timezone.utc).isoformat(),
            'bbox': list(bbox), 'coverage_complete': False, 'records': records, 'skipped': skipped}


def write_records(conn, data):
    with conn.transaction():
        for r in data['records']:
            conn.execute('''INSERT INTO public.fema_flood_zones
                (object_id, flood_zone, zone_subtype, sfha, source_citation, source_url, retrieved_at, geom)
                VALUES (%s,%s,%s,%s,%s,%s,%s,ST_SetSRID(ST_GeomFromGeoJSON(%s),4326))
                ON CONFLICT (object_id) DO NOTHING''',
                (r['object_id'], r['flood_zone'], r['zone_subtype'], r['sfha'],
                 r['source_citation'], data['source'], data['retrieved_at'], json.dumps(r['geometry'])))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='Apply reviewed additive schema and insert pilot')
    parser.add_argument('--limit', type=int, default=100)
    args = parser.parse_args()
    try:
        with connect() as conn:
            before = parcel_fingerprint(conn)
            conn.commit()
            data = download(conn, args.limit)
            DATA.parent.mkdir(parents=True, exist_ok=True)
            DATA.write_text(json.dumps(data))
            if args.write:
                with conn.transaction():
                    conn.execute(Path(__file__).with_name('schema.sql').read_text())
                write_records(conn, data)
            after = parcel_fingerprint(conn)
            if before != after:
                raise RuntimeError('Parcel fingerprint changed; investigate concurrent team writes')
            print(json.dumps({'downloaded': len(data['records']), 'skipped': data['skipped'],
                              'write': args.write, 'parcel_count': after[0], 'parcels_unchanged': True,
                              'coverage_complete': False, 'data_file': str(DATA)}))
        return 0
    except Exception as exc:
        print('FEMA pilot failed: ' + type(exc).__name__)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
