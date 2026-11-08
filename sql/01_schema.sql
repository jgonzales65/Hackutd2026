\connect CASCADE

CREATE TABLE IF NOT EXISTS properties (
    property_id TEXT PRIMARY KEY,
    name TEXT NOT NULL, 
    address TEXT, 
    city TEXT,
    county TEXT DEFAULT 'Bexar',
    state TEXT DEFAULT 'TX',
    lat DOUBLE PRECISION NOT NULL, 
    lon DOUBLE PRECISION NOT NULL, 
    property_type TEXT,
    assessed_value TEXT,
    source TEXT DEFAULT 'seed',
    updated_at TIMESTAMP DEFAULT now(),
);

CREATE TABLE IF NOT EXISTS systems (
    system_id TEXT PRIMARY KEY, 
    property_id TEXT REFERENCES properties(property_id) ON DELETE CASCADE,
    system_type TEXT NOT NULL,
    name TEXT,
    depends_on TEXT, 
    status TEXT DEFAULT 'ok', 
    sythetic BOOLEAN DEFAULT TRUE,
);

CREATE TABLE IF NOT EXISTS  property_risk(
    property_id TEXT PRIMARY KEY REFERENCES properties(property_id) ON DELETE CASCADE,
    flood_risk TEXT,
    in_flood_hazard_zoon BOOLEAN,
    elevation_ft DOUBLE PRECISION,
    epa_facility_count INT,
    tract_geoid TEXT,
    median_icome INT,
    population INT,
    risk_score DOUBLE PRECISION,
    data_quality JSONB,
    last_refreshed TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS documents(
    doc_id SERIAL PRIMARY KEY,
    property_id TEXT REFERENCES properties(property_id) ON DELETE CASCADE,
    doc_type TEXT,
    parsed JSONB,
    source_file TEXT,
    parsed_at TIMESTAMP DEFAULT now(),
);

CREATE TABLE IF NOT EXISTS alerts(
    alert_id TEXT PRIMARY KEY,
    state TEXT,
    severity TEXT,
    event TEXT,
    headline TEXT,
    area_desc TEXT,
    source TEXT DEFAULT 'NWS',
    sent_at TIMESTAMPZ,
    fetched_at TIMESTAMPz DEFAULT now()
);