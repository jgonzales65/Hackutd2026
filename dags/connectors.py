"""Public-data connectors. Each returns a small dict and raises on failure;
the DAG records failures in data_quality instead of crashing the pipeline."""
from common import get_json


def fema_flood(lat, lon):
    data = get_json(
        "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query",
        {"geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "inSR": 4326,
         "spatialRel": "esriSpatialRelIntersects", "outFields": "FLD_ZONE,SFHA_TF",
         "returnGeometry": "false", "f": "json"},
    )
    feats = data.get("features", [])
    if not feats:
        return {"flood_zone": None, "in_flood_hazard": False}
    a = feats[0]["attributes"]
    return {"flood_zone": a.get("FLD_ZONE"), "in_flood_hazard": a.get("SFHA_TF") == "T"}


def usgs_elevation(lat, lon):
    data = get_json("https://epqs.nationalmap.gov/v1/json",
                    {"x": lon, "y": lat, "wkid": 4326, "units": "Feet", "includeDate": "false"})
    return {"elevation_ft": float(data["value"])}


def epa_facilities(lat, lon, radius_mi=1):
    data = get_json("https://echodata.epa.gov/echo/echo_rest_services.get_facilities",
                    {"output": "JSON", "p_lat": lat, "p_long": lon, "p_radius": radius_mi})
    return {"epa_facility_count": int(data["Results"]["QueryRows"])}


def census_tract(lat, lon):
    geo = get_json("https://geocoding.geo.census.gov/geocoder/geographies/coordinates",
                   {"x": lon, "y": lat, "benchmark": "Public_AR_Current",
                    "vintage": "Current_Current", "format": "json"})
    t = geo["result"]["geographies"]["Census Tracts"][0]
    state, county, tract = t["STATE"], t["COUNTY"], t["TRACT"]
    acs = get_json("https://api.census.gov/data/2022/acs/acs5",
                   {"get": "B19013_001E,B01003_001E", "for": f"tract:{tract}",
                    "in": f"state:{state} county:{county}"})
    inc, pop = acs[1][0], acs[1][1]
    clean = lambda v: int(v) if v not in (None, "") and int(v) >= 0 else None  # noqa: E731
    return {"tract_geoid": t["GEOID"], "median_income": clean(inc), "population": clean(pop)}


def nws_alerts(state="TX"):
    data = get_json("https://api.weather.gov/alerts/active", {"area": state})
    out = []
    for f in data.get("features", []):
        p = f["properties"]
        out.append({"alert_id": p["id"], "state": state, "severity": p.get("severity"),
                    "event": p.get("event"), "headline": p.get("headline"),
                    "area_desc": p.get("areaDesc"), "sent_at": p.get("sent")})
    return out
