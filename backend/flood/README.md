# FEMA parcel flood overlap — hackathon pilot

Implemented on `feature/fema-parcel-overlap`. This module leaves teammate files and the existing parcels table intact. It complements the point lookup in `dags/connectors.py` with whole-parcel PostGIS intersection. It runs separately from the analytics API, avoiding its ML startup dependencies.

## Run the frontend-facing API now

From the repository root, using the existing ignored `backend/ingestion/.env` containing `SUPABASE_DB_URL`:

```bash
backend/.venv/bin/python -m pip install -r backend/flood/requirements.txt
backend/.venv/bin/python -m uvicorn backend.flood.api:app --host 0.0.0.0 --port 8001
```

Interactive API documentation: http://localhost:8001/docs

```bash
curl http://localhost:8001/api/parcels/100445/flood-risk
```

Frontend example (set the backend URL to the actual API host when deployed):

```javascript
const response = await fetch(`${backendUrl}/api/parcels/${encodeURIComponent(parcelId)}/flood-risk`);
if (!response.ok) throw new Error(`Flood assessment unavailable (${response.status})`);
const flood = await response.json();
// Render true as a mapped hazard overlap; null as unknown.
// Show fema_zone_classifications, matches, source and assessment_status.
```

Local CORS defaults: localhost ports 3000 and 5173. For another frontend host, set `FLOOD_CORS_ORIGINS` to comma-separated origins before starting the API. Keep database credentials on the backend. The API returns public geographic classifications only; 503 errors contain no driver details. No API deployment or frontend change is included.

## Verified with live data November 8, 2026

- Official FEMA National Flood Hazard Layer [Flood Hazard Zones, layer 28](https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28).
- Query envelope derived from the existing 1,996 parcels: longitude -98.5499844635298 to -98.4431716951038; latitude 29.3796628627798 to 29.4729725340441.
- Bounded query retrieved 100 actual polygons: 7 A, 20 AE, 2 AO, 71 X; no invalid polygons skipped. Polygons are not clipped to the query envelope.
- Imported into separate `public.fema_flood_zones`; GiST index; RLS enabled without browser policies. Backend uses the existing server database owner connection.
- 704 distinct parcels intersect at least one imported polygon; 90 intersect polygons with FEMA `SFHA_TF=T`.
- Real HTTP 200: parcel `100445` intersects FEMA object `28820159`, zone `AE`, citation `48029C_STUDY1`. Additional SFHA demo parcels: `100449`, `100450`.
- Real HTTP 200: parcel `101467` has no pilot match and returns null/`coverage_incomplete`. Missing parcel returns HTTP 404.
- Before/after parcel count and hash of every entire parcel row matched exactly during import: 1,996 unchanged rows.
- Original 13 tests passed. Seven new offline tests and two live read-only PostGIS tests passed. Live tests cover synthetic overlap, boundary contact, disjoint shapes, holes, and an actual parcel/SFHA overlap. Synthetic coordinates exist only in tests.

## Response meaning and limits

`mapped_flood_hazard_overlaps=true` means an intersecting polygon has `SFHA_TF=T` or the official subtype identifies `0.2 PCT ANNUAL CHANCE` flood hazard. `special_flood_hazard_area_overlaps=true` specifically requires `SFHA_TF=T`. An X classification alone does not establish hazard: FEMA X includes both minimal hazard and shaded 0.2% areas, so `zone_subtype` is retained.

This is deliberately a **partial pilot**. `coverage_complete` is always false. Without a positive hazard intersection, overlap fields remain null, including parcels intersecting only minimal-hazard X polygons. A missing match never means safe or confirmed absence of flood risk. Classifications describe FEMA mapped geography, not property-specific flood probabilities or financial losses. `ST_Intersects` includes boundary contact, so results do not imply positive-area overlap. All intersecting classifications are returned; none is silently selected as the sole zone.

Statuses: `overlap_found_partial_coverage`, `coverage_incomplete`, `hazard_data_unavailable`, `parcel_geometry_unavailable`. A database outage is HTTP 503; an unknown parcel is HTTP 404.

## Reproduce ingestion (already completed; no need before demo)

Review `schema.sql` before writing. Default invocation only downloads, validates, and saves an ignored local dataset; it queries the database read-only for bounds and fingerprints.

```bash
backend/.venv/bin/python -m backend.flood.ingest --limit 100
# Applies reviewed additive schema; inserts only into the FEMA table.
backend/.venv/bin/python -m backend.flood.ingest --write --limit 100
```

Hard cap is 200 source polygons per invocation; no county-wide mode or automatic pagination. Existing FEMA IDs are preserved via `ON CONFLICT DO NOTHING`; this is an insert-only demo, not a refresh service. Downloads and timestamps are saved under ignored `backend/ingestion/data/fema-pilot.json`. API responses include each stored polygon's retrieval time and official source citation. Errors stop the importer; invalid polygons are skipped and reported, never silently repaired. A future authoritative refresh/coverage audit is outside this pilot.

## Tests

```bash
backend/.venv/bin/python -m unittest discover -s backend/tests -v
# Opt-in: connects to existing Supabase, read-only; requires the pilot already imported.
RUN_FLOOD_DB_TESTS=1 backend/.venv/bin/python -m unittest discover -s backend/tests -v
```

Before submission: start the API, give the frontend developer its host/port and demo IDs above, and verify the frontend displays null as unknown. Push/merge still requires your approval.
