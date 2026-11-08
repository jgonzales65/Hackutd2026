# BCAD parcel ingestion

This component targets the **existing** Supabase project `xswkanpjxvosdtdzvjvl` and its existing `public.parcels` table. It creates no tables, policies, extensions, or database functions. Do not start the repository's Docker database for this task.

## What the files do

- `import_parcels.py`: bounded API downloads, field/geometry validation, retries, checkpoints, read-only schema/RLS inspection, and optional parameterized database inserts.
- `requirements.txt`: dependencies used only by this component: requests (HTTP), Shapely (geometry validation), psycopg (PostgreSQL), python-dotenv (local environment).
- `.env.example`: credential placeholders; contains no usable secrets.
- `../tests/test_import_parcels.py`: automated offline tests using mocked HTTP and database connections.
- Root `.gitignore`: ignores local environment files, virtual environments, checkpoints, and this component's downloaded datasets.

The checked-out repository contained no backend application code, Supabase client, migrations, or RLS definitions. Consequently the live database's policies/schema have **not** been verified during implementation. The preflight command below inspects the live database read-only. It also runs automatically before a write invocation. Existing teammate files and the Docker configuration are left as found.

## Data flow

BCAD GeoJSON → check response/error/CRS → require ascending OBJECTIDs → validate positive PropID and nonblank Situs → validate and normalize geometry → optionally commit a page to `public.parcels` → atomically save the last OBJECTID locally.

`PropID` becomes the canonical integer string `parcel_id`. `Situs` becomes `formatted_address`; mailing addresses and `Geo_id` are never substituted. `land_value` and `zoning_code` are explicitly NULL on new rows. Existing parcel rows are left intact, including their values and boundaries, through `ON CONFLICT (parcel_id) DO NOTHING`. Re-running from the beginning is safe; this is an insert-only importer, not a synchronization/update job.

Polygon coordinates get one extra nesting level to become MultiPolygon. MultiPolygons and interior holes are preserved. Rings must be closed and have at least four positions; coordinates must be finite 2D longitude/latitude within EPSG:4326 bounds. Shapely rejects empty, zero-area, and topologically invalid geometries. Invalid records are skipped with an OBJECTID and reason; shapes are not silently repaired. The API is asked for `outSR=4326`; absent GeoJSON CRS uses longitude/latitude, while unexpected explicit CRS fails validation. Bounds alone cannot prove a source has correctly declared its CRS.

The writer passes **only the geometry fragment** as a SQL parameter to `public.ST_GeomFromGeoJSON`, and explicitly assigns SRID 4326. No uncertain Supabase REST geometry serialization is used. See [PostGIS documentation](https://postgis.net/docs/ST_GeomFromGeoJSON.html). Pagination uses `OBJECTID > last_committed_id`, ordered ascending, rather than an offset; see [ArcGIS query documentation](https://developers.arcgis.com/rest/services-reference/enterprise/query-feature-service-layer/).

## Commands in the VS Code terminal

Run from the repository root:

```bash
cd /Users/izzy/Desktop/Hackutd2026
# Only if backend/.venv does not already exist:
python3 -m venv backend/.venv
source backend/.venv/bin/activate
python -m pip install -r backend/ingestion/requirements.txt
python -m unittest discover -s backend/tests -v
python backend/ingestion/import_parcels.py --dry-run --limit 100 --batch-size 100
```

Dry-run is the default and never opens a database connection. `--limit` counts **source features examined**, including invalid records and duplicates, rather than promising that many inserts. Memory is bounded to a page (batch size 1–1000). Within a page duplicate IDs are counted; dry-run does not query the database or retain a county-wide ID set. Database uniqueness protects against duplicates across pages and runs.

An implementation verification on November 8, 2026 retrieved exactly 100 real records: 100 valid, zero skipped, zero inserted, ending at OBJECTID 4102. That verification used `.state/verification-100.json`, leaving the default dry-run checkpoint available for your first run.

Checkpoint files persist locally in ignored `.state/`. To continue after failure, repeat the same command with `--resume`. The limit is per invocation, so a resume with `--limit 100` examines up to 100 **additional** source features. To intentionally start again, choose a new checkpoint path:

```bash
python backend/ingestion/import_parcels.py --dry-run --limit 100 --checkpoint backend/ingestion/.state/review-100.json
```

The importer refuses to overwrite an existing checkpoint without `--resume`. Dry-run and write checkpoints are separate and cannot be interchanged. Do not run two processes against the same checkpoint. Do not reuse write checkpoints with a different database or source. Source edits during a long run are not a consistent snapshot: changes to earlier OBJECTIDs require a fresh scan; existing rows still will not update.

## Credentials and read-only preflight

```bash
cp backend/ingestion/.env.example backend/ingestion/.env
```

Open the new `.env` locally in VS Code and replace the placeholder with the **PostgreSQL connection string from the existing project's Connect panel**. Verify the project reference is `xswkanpjxvosdtdzvjvl`. Use a direct connection or session pooler appropriate to your network, with the exact host/user/port supplied by Supabase. URL-encode special characters in the password. Use a server-side database role authorized for ingestion; an anon/publishable API key is not a PostgreSQL password. No service-role API token is needed. Never put this value in a browser-exposed `NEXT_PUBLIC_` variable, paste it into logs, or commit it. An existing shell environment variable takes precedence over `.env`.

```bash
python backend/ingestion/import_parcels.py --preflight
```

This command makes **only read-only database queries**, inspecting columns, MultiPolygon/SRID/dimension, unique index, role privileges, RLS flags, and existing policy definitions. It makes no API downloads and changes no schema or policies. Policy names/commands/roles are reported; policy expressions are not printed. Review conditions with the database owner: schema/privilege checks do not prove that every row will satisfy RLS. Do not disable RLS to make an import work. See [Supabase RLS documentation](https://supabase.com/docs/guides/database/postgres/row-level-security).

## Controlled database import — only after explicit approval

No database write was executed during implementation. First review the dry-run and preflight with the team, and obtain explicit approval for this command:

```bash
python backend/ingestion/import_parcels.py --write --limit 100 --batch-size 100
```

A page is one transaction. A database failure rolls back that page and leaves its checkpoint unchanged. If the database commits but saving the checkpoint fails, replay safely skips existing IDs. HTTP failures (including ArcGIS error objects in HTTP 200 responses) retry up to three times after the initial attempt with exponential delays. Requests have 10-second connection and 60-second read timeouts. All errors stop with a nonzero exit status; driver error text is suppressed to avoid credential leaks.

## Confirm geographic boundaries

After an approved import, run these read-only queries in the existing Supabase SQL Editor:

```sql
SELECT count(*) AS total_parcels,
       count(*) FILTER (WHERE geom IS NULL) AS missing_boundaries,
       count(*) FILTER (WHERE geom IS NOT NULL AND
         (NOT public.ST_IsValid(geom) OR public.ST_IsEmpty(geom)
          OR public.ST_SRID(geom) <> 4326
          OR public.GeometryType(geom) <> 'MULTIPOLYGON'
          OR public.ST_NDims(geom) <> 2)) AS invalid_boundaries
FROM public.parcels;

SELECT parcel_id, formatted_address,
       public.ST_SRID(geom) AS srid,
       public.ST_IsValid(geom) AS valid,
       public.ST_AsGeoJSON(geom) AS boundary
FROM public.parcels
ORDER BY created_at DESC
LIMIT 10;
```

These inspect all existing team rows, so a failing row may predate this importer. For individual parcels, compare the boundary on the team's map to the situs address and the BCAD source; valid geometry alone does not prove a correct real-world location. The importer's progress reports count rows inserted in that invocation; existing IDs may make this count smaller than the valid count.

## Before a full-county run

Obtain separate explicit approval for the full-county operation. First pass the read-only preflight, complete and review the controlled 100-record write, inspect geometry/map placement, confirm RLS with the database owner, and confirm database capacity and the team's backup/recovery approach. Agree on API load and batch size. Use the same database and preserve the write checkpoint when continuing the pilot:

```bash
# ONLY after separate full-county approval:
python backend/ingestion/import_parcels.py --write --full-county --batch-size 100 --resume
```

If starting from scratch instead, use a new write checkpoint and omit `--resume`. Full-county work is never implied by changing the batch size: it requires the explicit `--full-county` flag. No push, merge, shared schema change, or full-county import is part of this implementation.
