import { NextResponse } from 'next/server';
import { database } from '@/lib/db';


export async function GET(request: Request) {
  const params = new URL(request.url).searchParams;
  const id = params.get('id');
  const raw = params.get('bbox')?.split(',');
  const bbox = raw?.map(Number);
  if (id ? !/^\d{1,50}$/.test(id) : !bbox || bbox.length !== 4 || raw?.some(v => !v.trim()) ||
      bbox.some(v => !Number.isFinite(v)) || bbox[0] < -180 || bbox[2] > 180 ||
      bbox[1] < -90 || bbox[3] > 90 || bbox[0] >= bbox[2] || bbox[1] >= bbox[3] ||
      bbox[2] - bbox[0] > 2 || bbox[3] - bbox[1] > 2) {
    return NextResponse.json({ error: 'Supply a valid bbox=west,south,east,north (maximum 2 degrees), or numeric parcel id.' }, { status: 400 });
  }
  let client;
  try {
    client = await database().connect();
    await client.query('BEGIN READ ONLY');
    const available = await client.query("SELECT to_regclass('public.fema_flood_zones') IS NOT NULL AS available");
    const floodAvailable = available.rows[0].available;
    const result = await client.query(`
      SELECT p.parcel_id, p.formatted_address, ST_AsGeoJSON(p.geom)::json AS geometry,
        ${floodAvailable ? `(SELECT COALESCE(json_agg(json_build_object(
          'zone',z.flood_zone,'subtype',z.zone_subtype,'sfha',z.sfha,
          'source',z.source_url,'citation',z.source_citation,'retrievedAt',z.retrieved_at)
          ORDER BY z.object_id),'[]'::json)
          FROM public.fema_flood_zones z WHERE ST_Intersects(p.geom,z.geom))` : `'[]'::json`} AS flood
      FROM (SELECT parcel_id,formatted_address,geom FROM public.parcels
        WHERE ${id ? 'parcel_id=$1' : 'geom && ST_MakeEnvelope($1,$2,$3,$4,4326) AND ST_Intersects(geom,ST_MakeEnvelope($1,$2,$3,$4,4326))'}
        ORDER BY parcel_id LIMIT 501) p`, id ? [id] : bbox);
    await client.query('COMMIT');
    const parcels = result.rows.slice(0,500).map(row => ({
      id: row.parcel_id, address: row.formatted_address, zip: '', owner: 'Not available',
      score: null, breakdown: { flood: null, title: null, permits: null, zoning: null },
      findings: [], geometry: row.geometry,
      // Existing boundary sketch uses the first component; map uses the full geometry.
      coordinates: row.geometry.type === 'MultiPolygon' ? row.geometry.coordinates[0] : row.geometry.coordinates,
      flood: { available: floodAvailable, coverageComplete: false, matches: row.flood },
    }));
    return NextResponse.json({ parcels, truncated: result.rows.length > 500, limit: 500 },
      { headers: { 'Cache-Control': 'no-store' } });
  } catch {
    if (client) await client.query('ROLLBACK').catch(() => {});
    return NextResponse.json({ error: 'Parcel data unavailable. Check the server database connection and retry.' }, { status: 503 });
  } finally { client?.release(); }
}
