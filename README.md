# Hackutd2026
TerrainTel — Geospatial Real Estate Intelligence
HackUTD 2026 | CBRE Challenge

TerrainTel is a geospatial real estate intelligence platform built to make property due diligence easier to navigate. It brings together parcel boundaries, public property records, ownership information, and risk-related data so users can investigate a property in one place rather than searching across disconnected sources.

Our hackathon prototype focuses on Bexar County, Texas, with an architecture designed to support additional data sources and geographic coverage over time.
Why we built it
Real estate due diligence can involve county appraisal databases, maps, legal records, environmental information, and financial analysis. These sources are often difficult to connect, especially when records use different identifiers or geographic formats.

We wanted to build a map-centered tool that helps investors and real estate professionals answer a simple question: What should I know about this property before making a decision?
Key capabilities
- Real property data: Ingests parcel records from the Bexar County Appraisal District's ArcGIS service.
- Geospatial storage: Stores parcel boundaries as PostGIS MULTIPOLYGON geometries in EPSG:4326.
- Reliable ingestion: Uses pagination, geometry validation, duplicate handling, batch writes, and checkpoints for resumable imports.
- Property data foundation: Includes database structures for parcels, entities, entity relationships, and title encumbrances.
- Interactive frontend: A Next.js-based parcel-app uses MapLibre GL for the property-map experience.
- Risk intelligence direction: Designed to connect property records to environmental, legal, ownership, and financial risk information.
Prototype status: The parcel ingestion pipeline and shared geospatial database have been tested. Live database-to-map integration and some risk-analysis features may depend on the branch and configuration being run; do not assume every planned feature is available in the current build.

Tech stack
Layer	Technologies
Frontend	Next.js, React, MapLibre GL (maplibre-gl@4.7.1)
Backend and ingestion	Python
Database	Supabase PostgreSQL, PostGIS
Property data	Bexar County Appraisal District (BCAD) ArcGIS API
Development	Git, GitHub, AI-assisted development and testing


Project structure
Hackutd2026/
├── backend/                 # Python data ingestion, backend work, and tests
│   ├── ingestion/
│   │   └── import_parcels.py
│   └── tests/
├── parcel-app/              # Next.js / MapLibre frontend (UI integration branch)
├── sql/                     # SQL definitions and queries
├── dags/                    # Data workflow-related files
├── Data/                    # Data assets
├── docker-compose.yml       # Optional local PostgreSQL/PostGIS container
└── README.md
Some directories or files may differ between main and the team's feature branches.
Getting started
Prerequisites
- Git
- Node.js and npm
- Python 3 and venv
- Access to the team's Supabase project, if using the live database
1. Clone the repository
git clone https://github.com/jgonzales65/Hackutd2026.git
cd Hackutd2026
If the updated UI has not yet been merged into main, check out the integration branch:
git fetch origin
git switch feature/ui-database-integration
If that branch is only available remotely, create a local tracking branch for it instead.
2. Run the frontend
From the repository root:
cd parcel-app
npm install
npm run dev
Open the local URL printed by the development server (normally http://localhost:3000).

Important: Run npm install inside parcel-app after pulling frontend changes. The application uses the pinned dependency maplibre-gl@4.7.1.
3. Configure the database and Python environment
Return to the repository root, then create a virtual environment:
cd ..
python3 -m venv backend/.venv
source backend/.venv/bin/activate
Install the Python packages listed by the backend's dependency configuration, if present.

The ingestion tooling uses a local environment file at backend/ingestion/.env with a database connection variable:
SUPABASE_DB_URL=your_database_connection_string
Use the credentials provided privately by the project owner. Never commit real connection strings, .env files, or service-role credentials to GitHub.
4. Validate or import parcel data
A safe first check is a dry run:
python backend/ingestion/import_parcels.py --dry-run --limit 100
To run the existing Python tests:
python -m unittest discover -s backend/tests -v
The importer also supports live database writes, batching, and checkpoints. Only use --write with the team's approval because it modifies the shared database.
Data pipeline
BCAD ArcGIS parcel service
          |
          v
Python parcel importer
  - fetches and paginates records
  - checks parcel IDs and addresses
  - validates and normalizes geometries
  - skips duplicates / saves checkpoints
          |
          v
Supabase PostgreSQL + PostGIS
          |
          v
Backend data access / GeoJSON integration
          |
          v
Next.js + MapLibre property map
The database-to-UI connection is the focus of the feature/ui-database-integration branch and should be verified against that branch before marking the full pipeline as complete.
Parcel import results
During development, the team tested an import of 2,000 source records. The result was:
- 1,996 valid parcel records stored in the shared database in total.
- 4 source records skipped because of missing/invalid addresses or invalid geometry.
- No missing or invalid parcel geometry in the verified stored dataset.
This is a working Bexar County sample, not a complete import of every parcel in the county.
Database overview
Table	Purpose
parcels	Property identifiers, addresses, parcel geometries, and available land/zoning fields
entities	Entity information for ownership-related analysis
entity_relationships	Relationships between entities
title_encumbrances	Data structure for property title and encumbrance information


Parcel geometries use PostGIS MULTIPOLYGON with SRID 4326. Some fields, such as land_value and zoning_code, may be empty when the source does not provide them.
Challenges and lessons learned
The biggest technical challenge was combining public records with real geographic data. Some county records had missing addresses, unusable identifiers, or invalid geometries. We also needed to handle Polygon versus MultiPolygon formats, avoid duplicate inserts, and coordinate different parts of the application across four team members.

The project gave us hands-on experience with public APIs, geospatial databases, frontend mapping, data validation, collaborative development, and testing under a hackathon deadline.
What's next
- Finish and verify live parcel selection and property details in the frontend.
- Connect implemented risk-scoring logic to the property interface.
- Add and validate environmental datasets such as FEMA flood zones.
- Expand ownership and title-data coverage.
- Improve risk explanations and property comparisons.
- Extend the system beyond the initial Bexar County prototype.
Team and event
Built by a four-person team at HackUTD 2026 for a real estate intelligence challenge inspired by CBRE.
Repository
github.com/jgonzales65/Hackutd2026
