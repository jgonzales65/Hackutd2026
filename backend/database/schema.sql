-- ==========================================
-- TERRACINTEL DATABASE SCHEMA
-- ==========================================
-- 1. Enable PostGIS Spatial Extension
CREATE EXTENSION IF NOT EXISTS postgis;
-- 2. Master Table: Parcels (Geospatial Boundaries & Core Info)
CREATE TABLE IF NOT EXISTS public.parcels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parcel_id VARCHAR(50) UNIQUE NOT NULL,
    formatted_address TEXT NOT NULL,
    land_value NUMERIC(12, 2),
    zoning_code VARCHAR(20),
    geom GEOMETRY(Polygon, 4326),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);
-- Spatial index for high-performance map bounding-box queries
CREATE INDEX IF NOT EXISTS idx_parcels_geom ON public.parcels USING GIST (geom);
-- 3. Master Table: Entities (LLCs, Individuals, Trusts, Banks)
CREATE TABLE IF NOT EXISTS public.entities (
    entity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(150) NOT NULL,
    entity_type VARCHAR(50) NOT NULL -- 'INDIVIDUAL', 'LLC', 'TRUST', 'BANK'
);
-- 4. Dependent Table: Entity Relationships (Corporate Ownership Web / Graph Edges)
CREATE TABLE IF NOT EXISTS public.entity_relationships (
    relationship_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_entity_id UUID REFERENCES public.entities(entity_id) ON DELETE CASCADE,
    target_entity_id UUID REFERENCES public.entities(entity_id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL,
    ownership_percentage NUMERIC(5, 2) DEFAULT 100.00
);
-- 5. Dependent Table: Title Encumbrances (Liens, Mortgages, Clouded Titles)
CREATE TABLE IF NOT EXISTS public.title_encumbrances (
    encumbrance_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parcel_id UUID REFERENCES public.parcels(id) ON DELETE CASCADE,
    claimant_entity_id UUID REFERENCES public.entities(entity_id) ON DELETE
    SET NULL,
        encumbrance_type VARCHAR(50) NOT NULL,
        -- 'MECHANICS_LIEN', 'TAX_LIEN', 'MORTGAGE'
        amount NUMERIC(12, 2) NOT NULL,
        is_resolved BOOLEAN DEFAULT FALSE
);