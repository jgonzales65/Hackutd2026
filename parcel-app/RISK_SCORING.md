# Preliminary mapped flood severity

Method: `fema-zone-severity-v1`. Implemented in `lib/flood-scoring.ts` and invoked by the existing server-side `/api/parcels` route. No schema changes, writes, additional upstream downloads, or extra client scoring requests are needed. Computation uses the current database result per viewport request; the inexpensive scoring function is not persisted or cached independently of its source geometry, avoiding stale scores.

## Available evidence

Read-only inspection on November 8, 2026 found 1,996 parcels, 100 FEMA polygons, zero entities, zero title encumbrances, and no `property_risk` or `properties` enrichment tables. All parcel land values and zoning codes are null. No verified financial, other environmental, ownership/legal, permit, or zoning assessment can be calculated from those records.

Existing teammate implementations were inspected and preserved:

- `backend/analytics/risk_engine.py`: weighted four-domain composite. Missing inputs currently contribute zero and its thresholds differ from this request. It cannot support a complete assessment with only flood evidence.
- `backend/analytics/capex_calculator.py`: fixed cost benchmarks, without validated property land values or actual mitigation costs here. Not used to invent a financial score.
- `dags/enrich_property_risk.py`: point-based source enrichment with additional elevation/income heuristics. Its target enrichment tables are absent from the shared database; source failure can contribute zero. Not used as verified parcel assessments.

The existing PostGIS polygon data provides the working category. FEMA's [zone definitions](https://www.floodsmart.gov/flood-zones-and-maps/what-is-my-flood-zone) describe the source classifications; the [NFHL layer](https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28) supplies the actual geometry and attributes. The numerical values below are our application's ordinal severity index, not official FEMA ratings, calibrated flood probabilities, percent damage, or financial loss.

## Rules

For each parcel, use `ST_Intersects` with imported FEMA polygons. Include boundary contact; this is not a positive-area-overlap measurement. Use the maximum recognized intersecting severity, without summing overlapping polygons:

| Source classification | Required flag / subtype | Application score |
| --- | --- | --- |
| V / VE / numbered V zones, or floodway | SFHA true; floodway subtype exactly `FLOODWAY` | 90 |
| A / AE / AO / AH / AR / A99 / numbered A / dual AR zones | SFHA true | 65 |
| X | SFHA false; subtype exactly `0.2 PCT ANNUAL CHANCE FLOOD HAZARD` or `1 PCT FUTURE CONDITIONS` | 35 |
| X | SFHA false; subtype exactly `AREA OF MINIMAL FLOOD HAZARD` | 10, subject to full coverage rule |
| Unknown classifications, unknown/contradictory flags, unrecognized X subtype, no source data | Not enough supported evidence | null |

The difference between 35, 65, and 90 is a documented application prioritization choice. It is not inferred from flood depths or an estimated probability. Future-condition X is explicitly distinguished from minimal-hazard X; it is not claimed to be a present-day SFHA.

Classification thresholds apply consistently to map, table, details, and filters: 0–24 Low; 25–49 Moderate; 50–74 High; 75–100 Critical. Null is Not assessed (blue-gray).

## Coverage and availability

Low scores require the **entire parcel geometry** to be covered by the union of the intersecting imported polygons, evaluated with `ST_CoveredBy(parcel, ST_UnaryUnion(ST_Collect(zones)))`, and all intersecting classifications must be recognized. A fragment of a minimal-hazard polygon never establishes a low score. Even full parcel coverage describes the imported mapped classifications only; it does not establish safety from all flood mechanisms or complete regional NFHL coverage.

A positive recognized hazard with partial coverage yields a **minimum observed severity**. Missing polygons or unrecognized intersecting zones may raise that score later. This lower-bound status is separate from severity. Regional pilot coverage is always incomplete. Unknown classifications do not get zero points.

`score` remains null for overall property risk. `assessment.score` contains flood severity; `assessment.scope` is `flood_only`. `breakdown.flood` contains the same value. Map/table/summary use the flood value with explicit flood-only labels; all unavailable category values remain null. Sources, citations, retrieval times, and the per-zone score are returned in `assessment.evidence`. Other missing categories are listed in `assessment.missingCategories`. The details panel also displays the method, explanation, and coverage status.

## Verification and demo

From the repository root:

```bash
node --test parcel-app/tests/flood-scoring.test.mjs
RUN_FLOOD_DB_TESTS=1 backend/.venv/bin/python -m unittest discover -s backend/tests -v
cd parcel-app
npm run lint
npm run build
npm run dev
```

Scoring unit tests use Node's native TypeScript support (Node 22.18+; verified on Node 25). Open http://localhost:3000. Endpoints:

- `/api/parcels?id=100445`: actual AE/SFHA intersection, flood score 65 / High, minimum observed severity because coverage is partial; overall null.
- `/api/parcels?id=100052`: actual minimal-hazard X polygon covers the full parcel, flood score 10 / Low; overall null.
- `/api/parcels?id=101467`: no imported match, flood null / Not assessed; overall null.

Verified in Chromium against the production server: all three API responses, selection changes for all three parcels, the High filter, noncollapsed map, and zero browser runtime errors. Map colors were visually inspected; high flood parcels render red and unknown parcels blue-gray. Seven scoring tests and all 22 existing backend tests passed. Critical coastal/floodway rules are unit-tested with fixtures but are not present in this Bexar pilot; they are not claimed as live demo cases.

Existing address search is scoped to the viewport. To reproduce selection of an ID outside the current view without changing application data, save the actual parcel ID in the browser watchlist or navigate the map to its area. No complete overall assessment is currently available, because the other verified risk categories are missing.
