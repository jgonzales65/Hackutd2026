This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.


## Real Bexar County parcels

Run `npm install` and `npm run dev` from `parcel-app`, then open http://localhost:3000.
The existing server-only `backend/ingestion/.env` is loaded automatically for local development.
Alternatively configure `SUPABASE_DB_URL` in the server environment or ignored `parcel-app/.env.local`.
Use the existing Supabase PostgreSQL URL with TLS (`sslmode=require`); never use a `NEXT_PUBLIC_` credential.
For hosting, set the server environment variable; the local ingestion file is not bundled for deployment.
No separate Python API is required by this UI.

The same-origin `GET /api/parcels?bbox=west,south,east,north` endpoint runs parameterized,
read-only PostGIS queries against `public.parcels`. Bounding boxes are required, validated,
and limited to two degrees on each axis. Responses have `{ parcels, truncated, limit }`, with
at most 500 parcels, and `Cache-Control: no-store`. Zoom in when the response is truncated.
`GET /api/parcels?id=100445` retrieves a single parcel for saved selections. Invalid parameters
return 400; unavailable database returns a sanitized 503. No schema changes are required.

The map starts over the imported Bexar area and queries after moving, with a 250 ms debounce
and cancellation of obsolete requests. Full MultiPolygon boundaries and holes are preserved.
Clicking a boundary or table row shows its actual property ID and situs address. Existing
search operates on the loaded viewport; the watchlist can reload saved IDs outside that view.
Empty views, loading, retryable API errors, and map resource errors have explicit messages.

Existing `public.fema_flood_zones` data is included when available, with FEMA zones, subtypes,
SFHA flags, source citations and retrieval dates. Pilot coverage remains incomplete: no match
means unknown flood overlap. Missing owner, ZIP, overall scores and category scores are shown
as unavailable/unassessed, without fabricated risk numbers or closing recommendations.
The existing score filters only include parcels with known scores, so unassessed parcels appear
under “All parcels.” The basemap still uses the original MapLibre/OpenStreetMap configuration;
MapLibre is pinned to exactly 4.7.1.

Verification: `npm run build`; from repository root,
`RUN_FLOOD_DB_TESTS=1 backend/.venv/bin/python -m unittest discover -s backend/tests -v`.
A live HTTP check of `/api/parcels?id=100445` should show an actual address and FEMA AE match.
