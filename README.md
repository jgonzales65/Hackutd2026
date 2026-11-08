
# Parcel Intelligence

### Geospatial Real Estate Risk & Property Intelligence Platform

**HackUTD 2026 | CBRE Challenge**

Parcel Intelligence is a full-stack geospatial real estate intelligence platform designed to simplify property research, due diligence, and investment risk analysis.

Our application combines real property records, geographic boundaries, ownership information, and risk-related data into a centralized, interactive platform. Instead of searching through multiple government databases and disconnected resources, users can explore property information through a single map-based interface.

Built during HackUTD 2026, our application focuses on **Bexar County, Texas**, with an architecture designed to support expansion into additional regions.

## Inspiration

Real estate due diligence involves researching many factors, including property boundaries, ownership history, zoning, environmental hazards, and financial risks.

Unfortunately, this information is often scattered across different government websites, public records, and databases.

Inspired by the CBRE Challenge, our team wanted to create a platform that brings these resources together and makes property research more efficient, accessible, and understandable.

Our goal was to answer one question:

**What should someone know about a property before investing in it?**

## Key Features

### Interactive Geospatial Map
- Interactive property visualization using MapLibre GL
- Real property boundaries retrieved from our database
- Clickable parcels with detailed property information
- Geographic exploration of Bexar County
- Dynamic frontend connected to our backend

### Real Property Data
- Bexar County Appraisal District (BCAD) data integration
- Real parcel boundaries and property addresses
- Unique parcel identification
- Property attributes and geographic information
- Centralized storage in Supabase PostgreSQL

### Property Intelligence
- Property ownership and entity relationships
- Title and encumbrance data structures
- Geographic property analysis
- Risk-related property information
- Centralized property detail views

### Automated Data Processing
- Python-based data ingestion
- ArcGIS REST API integration
- Automated pagination and batch processing
- Geometry validation and normalization
- Duplicate detection
- Checkpoint-based import recovery
- Error handling for incomplete records

### Full-Stack Integration
- Connected Next.js frontend and backend
- Live property data retrieved from Supabase
- PostGIS spatial queries
- GeoJSON-based geographic visualization
- Interactive property selection and information display

## Technology Stack

| Category | Technologies |
|----------|-------------|
| Frontend | Next.js, React |
| Mapping | MapLibre GL 4.7.1 |
| Backend | Python |
| Database | Supabase, PostgreSQL |
| Geospatial | PostGIS, GeoJSON |
| Data Integration | ArcGIS REST API |
| Data Source | Bexar County Appraisal District |
| Version Control | Git, GitHub |
| Development Tools | VS Code, ChatGPT, Codex |

## System Architecture

Parcel Intelligence integrates public property information with a geospatial database and an interactive web application.

```text
      Bexar County Appraisal District
                    |
                    v
              ArcGIS REST API
                    |
                    v
           Python Data Ingestion
                    |
                    v
          Supabase PostgreSQL
                + PostGIS
                    |
                    v
             Backend / API
                    |
                    v
            Next.js Frontend
                    |
                    v
         MapLibre Interactive Map
                    |
                    v
          Property Intelligence UI
```

Our backend processes real property information and stores geographic boundaries in PostGIS.

The frontend retrieves this information through the application's backend and displays the results through an interactive map and property information interface.

## Getting Started

### Prerequisites

Before running the application, make sure you have:

- Node.js
- npm
- Python 3
- Git
- Access to the project's Supabase database

### 1. Clone the Repository

```bash
git clone https://github.com/jgonzales65/Hackutd2026.git

cd Hackutd2026
```

### 2. Install Frontend Dependencies

Navigate to the frontend directory:

```bash
cd parcel-app
```

Install the dependencies:

```bash
npm install
```

**Important:** The frontend uses `maplibre-gl@4.7.1`. Run `npm install` inside `parcel-app` after pulling updated code.

### 3. Start the Frontend

```bash
npm run dev
```

Open the application in your browser:

http://localhost:3000

### 4. Configure the Backend

From the repository root, create a Python virtual environment:

```bash
python3 -m venv backend/.venv

source backend/.venv/bin/activate
```

Install the dependencies required by the backend configuration.

Configure the environment variables needed by your API and Supabase connection.

For the parcel ingestion pipeline, create:

```text
backend/ingestion/.env
```

Add the database connection string:

```dotenv
SUPABASE_DB_URL=your_database_connection_string
```

**Security:** Never commit database passwords, Supabase service-role keys, or `.env` files to GitHub.

Start the application's backend using the command specified in its backend configuration.

### 5. Test the Data Ingestion Pipeline

To validate the pipeline without modifying the database:

```bash
python backend/ingestion/import_parcels.py --dry-run --limit 100
```

Run the backend unit tests:

```bash
python -m unittest discover -s backend/tests -v
```

The ingestion pipeline supports batching, duplicate detection, and resumable imports.

## Database Architecture

Parcel Intelligence uses Supabase PostgreSQL with the PostGIS extension for geographic data storage and spatial analysis.

### Main Tables

| Table | Purpose |
|-------|---------|
| parcels | Property identification, addresses, attributes, and geographic boundaries |
| entities | Property ownership-related entities |
| entity_relationships | Connections between ownership entities |
| title_encumbrances | Property title and legal encumbrance information |

### Parcel Schema

The `parcels` table includes:

- `id` — Unique database identifier
- `parcel_id` — Unique property identifier
- `formatted_address` — Property address
- `land_value` — Available land valuation
- `zoning_code` — Available zoning information
- `geom` — PostGIS geographic geometry
- `created_at` — Record creation timestamp

Geographic boundaries are stored as `MULTIPOLYGON` geometries using SRID 4326.

PostGIS enables efficient geographic queries and allows property boundaries to be displayed through GeoJSON.

## Real-World Data Processing

Our team implemented a Python ingestion pipeline that retrieves real parcel records from the Bexar County Appraisal District's ArcGIS service.

### Import Results

| Metric | Result |
|--------|--------|
| Records processed | 2,000 |
| Valid parcels stored | 1,996 |
| Invalid records skipped | 4 |
| Missing geometries | 0 |
| Invalid stored geometries | 0 |

The pipeline successfully handles inconsistent data, validates geographic boundaries, and prevents duplicate records.

These results represent our initial imported dataset, not the entirety of Bexar County.

## Challenges We Faced

### Working with Real Government Data

Unlike sample datasets, real property records are not always complete or consistent.

We encountered missing addresses, unusable property identifiers, and invalid geometric boundaries.

To address these issues, we implemented data validation, error handling, and filtering before storing records.

### Geographic Data Compatibility

Some parcels contain complex geographic shapes, including multiple polygons and interior boundaries.

We had to ensure our geographic data was valid and compatible with PostGIS and MapLibre.

### Connecting the Frontend and Database

A major part of our project involved integrating the interactive frontend with our existing Supabase database.

This required coordinating API responses, geographic data formats, property selection, and frontend state.

Successfully connecting these components allowed our application to display real property information rather than relying on placeholder data.

### Team Collaboration

Our team divided responsibilities across data ingestion, backend engineering, risk analysis, and frontend development.

Integrating these different components under a tight deadline required communication, debugging, and careful version control.

## What We Learned

Throughout HackUTD 2026, our team gained experience with:

- Integrating public government APIs
- Designing relational and geospatial databases
- Working with PostgreSQL and PostGIS
- Processing geographic information with Python
- Building interactive maps with MapLibre
- Connecting frontend and backend systems
- Developing data ingestion pipelines
- Collaborating through Git and GitHub
- Testing and debugging full-stack applications

One of our biggest takeaways was learning how much work goes into transforming raw public data into information that people can actually use.

## Future Improvements

Although we successfully developed a working full-stack application, we see opportunities to expand Parcel Intelligence.

Future improvements include:

- Expanding parcel coverage beyond Bexar County
- Incorporating additional environmental risk datasets
- Expanding FEMA flood-zone analysis
- Improving property ownership relationship visualization
- Adding additional zoning and development information
- Expanding financial risk modeling
- Developing AI-assisted property risk explanations
- Adding more advanced property comparison tools
- Supporting additional cities and counties

Our long-term goal is to develop a scalable platform that makes real estate research and risk intelligence more accessible.

## Our Team

Parcel Intelligence was developed by a four-person team during HackUTD 2026.

Our development responsibilities included:

**Data Engineering & API Integration**
- Public data collection
- API integration
- Data processing and ingestion

**Geospatial & Backend Engineering**
- Supabase and PostgreSQL
- PostGIS database architecture
- Geographic data validation
- Backend integration

**Risk Analysis & Modeling**
- Property risk analysis
- Financial and investment-related analysis
- Property intelligence features

**Frontend Development**
- Next.js and React
- MapLibre integration
- Interactive user interface
- Property visualization

## Hackathon

**Event:** HackUTD 2026

**Sponsor Challenge:** CBRE

**Project Name:** Parcel Intelligence

**Repository:** https://github.com/jgonzales65/Hackutd2026

---

### Disclaimer

Parcel Intelligence was developed as a hackathon project. Property information, ownership records, and risk assessments should be independently verified before making real estate, legal, or financial decisions.

