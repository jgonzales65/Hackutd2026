-- Additive only: no changes to public.parcels. Run with the database owner.
CREATE TABLE IF NOT EXISTS public.fema_flood_zones (
    object_id bigint PRIMARY KEY,
    flood_zone text NOT NULL,
    zone_subtype text,
    sfha boolean,
    source_citation text,
    source_url text NOT NULL,
    retrieved_at timestamptz NOT NULL,
    geom geometry(MultiPolygon, 4326) NOT NULL,
    CHECK (ST_IsValid(geom) AND NOT ST_IsEmpty(geom))
);
CREATE INDEX IF NOT EXISTS fema_flood_zones_geom_idx
    ON public.fema_flood_zones USING gist (geom);
ALTER TABLE public.fema_flood_zones ENABLE ROW LEVEL SECURITY;
-- No browser policies: access through the server-side API using the owner role.
