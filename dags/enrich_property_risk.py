"""DAG 2: enrich every property with public risk data. One mapped task per property,
and one mapped task per source inside it is overkill for a hackathon, so each property task
calls the four APIs and records which ones failed in data_quality."""
import json
from datetime import datetime, timedelta

from airflow.decorators import dag, task

import connectors
from common import conn

SOURCES = {
    "fema": connectors.fema_flood,
    "usgs": connectors.usgs_elevation,
    "epa": connectors.epa_facilities,
    "census": connectors.census_tract,
}


def score(r):
    s = 0.0
    if r.get("in_flood_hazard"):
        s += 40
    s += min((r.get("epa_facility_count") or 0) * 2, 30)
    if r.get("elevation_ft") is not None and r["elevation_ft"] < 600:
        s += 10
    if r.get("median_income") is not None and r["median_income"] < 40000:
        s += 10
    return min(s, 100.0)


@dag(dag_id="enrich_property_risk", start_date=datetime(2026, 11, 1), schedule="@daily", catchup=False,
     default_args={"retries": 2, "retry_delay": timedelta(seconds=30)}, tags=["bexar", "enrich"])
def enrich_property_risk():
    @task
    def list_properties():
        with conn() as c, c.cursor() as cur:
            cur.execute("SELECT property_id, lat, lon FROM properties ORDER BY property_id")
            return [{"property_id": a, "lat": b, "lon": d} for a, b, d in cur.fetchall()]

    @task(max_active_tis_per_dag=4)
    def enrich(p):
        result, quality = {}, {}
        for name, fn in SOURCES.items():
            try:
                result.update(fn(p["lat"], p["lon"]))
                quality[name] = "ok"
            except Exception as e:  # noqa: BLE001
                quality[name] = f"failed: {type(e).__name__}"
        result["risk_score"] = score(result)
        cols = ["flood_zone", "in_flood_hazard", "elevation_ft", "epa_facility_count",
                "tract_geoid", "median_income", "population", "risk_score"]
        vals = [result.get(k) for k in cols]
        with conn() as c, c.cursor() as cur:
            cur.execute(
                f"""INSERT INTO property_risk(property_id,{",".join(cols)},data_quality,last_refreshed)
                    VALUES(%s,{",".join(["%s"] * len(cols))},%s,now())
                    ON CONFLICT (property_id) DO UPDATE SET
                    {",".join(f"{k}=EXCLUDED.{k}" for k in cols)},
                    data_quality=EXCLUDED.data_quality, last_refreshed=now()""",
                [p["property_id"], *vals, json.dumps(quality)])
        return {"property_id": p["property_id"], **quality}

    enrich.expand(p=list_properties())


enrich_property_risk()
