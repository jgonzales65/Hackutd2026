-- 1. Create Nodes (Entities & Parcels)
CREATE TABLE IF NOT EXISTS public.entities (
    entity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(150) NOT NULL,
    entity_type VARCHAR(50) NOT NULL -- 'INDIVIDUAL', 'LLC', 'TRUST', 'BANK'
);
-- 2. Create Edges (Relationships & Transfers)
CREATE TABLE IF NOT EXISTS public.entity_relationships (
    relationship_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_entity_id UUID REFERENCES public.entities(entity_id),
    target_entity_id UUID REFERENCES public.entities(entity_id),
    relationship_type VARCHAR(50) NOT NULL,
    -- 'OWNS_SHELL_LLC', 'PARENT_COMPANY', 'HEIR_OF'
    ownership_percentage NUMERIC(5, 2) DEFAULT 100.00
);
CREATE TABLE IF NOT EXISTS public.title_encumbrances (
    encumbrance_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parcel_id UUID REFERENCES public.parcels(id),
    claimant_entity_id UUID REFERENCES public.entities(entity_id),
    encumbrance_type VARCHAR(50) NOT NULL,
    -- 'MECHANICS_LIEN', 'TAX_LIEN', 'MORTGAGE'
    amount NUMERIC(12, 2) NOT NULL,
    is_resolved BOOLEAN DEFAULT FALSE
);
-- 3. Recursive Graph Query: Uncover Ultimate Beneficial Ownership (UBO) through Shell LLC Chains
WITH RECURSIVE entity_graph AS (
    -- Anchor member: Select starting shell company owning parcel
    SELECT source_entity_id,
        target_entity_id,
        relationship_type,
        1 AS depth
    FROM public.entity_relationships
    WHERE source_entity_id = '00000000-0000-0000-0000-000000000001' -- Target LLC ID
    UNION ALL
    -- Recursive member: Traverse through parent ownership links
    SELECT r.source_entity_id,
        r.target_entity_id,
        r.relationship_type,
        g.depth + 1
    FROM public.entity_relationships r
        INNER JOIN entity_graph g ON r.source_entity_id = g.target_entity_id
    WHERE g.depth < 5 -- Prevent infinite loops
)
SELECT e1.name AS shell_company,
    r.relationship_type,
    e2.name AS ultimate_owner,
    r.depth
FROM entity_graph r
    JOIN public.entities e1 ON r.source_entity_id = e1.entity_id
    JOIN public.entities e2 ON r.target_entity_id = e2.entity_id;
-- 4. Multi-Party Lien & Cloudy Title Detection Query
SELECT p.parcel_id,
    p.formatted_address,
    COUNT(t.encumbrance_id) AS unresolved_liens_count,
    SUM(t.amount) AS total_lien_liability
FROM public.parcels p
    JOIN public.title_encumbrances t ON p.id = t.parcel_id
WHERE t.is_resolved = FALSE
GROUP BY p.id,
    p.parcel_id,
    p.formatted_address
HAVING COUNT(t.encumbrance_id) > 1;
-- Flag multi-party lien conflicts