"""Run on your own machine to check which public APIs respond:
    python3 dags/smoke_test.py
No Airflow or Docker needed (just `pip install requests psycopg2-binary`)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("WAREHOUSE_DSN", "postgresql://cascade:cascade@localhost:5432/cascade")
import connectors  # noqa: E402

LAT, LON = 29.4241, -98.4936
for name, fn, args in [("FEMA flood", connectors.fema_flood, (LAT, LON)),
                       ("USGS elevation", connectors.usgs_elevation, (LAT, LON)),
                       ("EPA ECHO", connectors.epa_facilities, (LAT, LON)),
                       ("Census tract+ACS", connectors.census_tract, (LAT, LON)),
                       ("NWS alerts", lambda s: connectors.nws_alerts(s)[:1], ("TX",))]:
    try:
        print(f"OK    {name}: {fn(*args)}")
    except Exception as e:  # noqa: BLE001
        print(f"FAIL  {name}: {type(e).__name__}: {e}")
