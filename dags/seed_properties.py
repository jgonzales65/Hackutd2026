"""DAG 1: load Bexar properties from the seed CSV and generate synthetic building systems.
Real property data goes here later (Bexar CAD export) by swapping the CSV reader."""
import csv
import os
from datetime import datetime

from airflow.decorators import dag, task

from common import conn

SYSTEM_TEMPLATE = [  # (type, name, depends_on_index)
    ("power", "Utility feeder", None),
    ("power", "Backup generator", 0),
    ("network", "Building controller", 0),
    ("hvac", "Chiller plant", 2),
    ("hvac", "Air handlers", 3),
    ("access_control", "Badge system", 2),
    ("fire", "Fire panel", 0),
]


@dag(dag_id="seed_properties", start_date=datetime(2026, 11, 1), schedule=None, catchup=False,
     tags=["bexar", "seed"])
def seed_properties():
    @task
    def load_properties():
        path = os.environ["SEED_CSV"]
        with open(path) as f, conn() as c, c.cursor() as cur:
            n = 0
            for r in csv.DictReader(f):
                cur.execute(
                    """INSERT INTO properties(property_id,name,address,city,lat,lon,property_type,assessed_value)
                       VALUES(%(property_id)s,%(name)s,%(address)s,%(city)s,%(lat)s,%(lon)s,%(property_type)s,%(assessed_value)s)
                       ON CONFLICT (property_id) DO UPDATE SET name=EXCLUDED.name, lat=EXCLUDED.lat,
                         lon=EXCLUDED.lon, assessed_value=EXCLUDED.assessed_value, updated_at=now()""", r)
                n += 1
        return n

    @task
    def generate_systems(_):
        with conn() as c, c.cursor() as cur:
            cur.execute("SELECT property_id FROM properties")
            for (pid,) in cur.fetchall():
                ids = [f"{pid}-S{i}" for i in range(len(SYSTEM_TEMPLATE))]
                for i, (stype, name, dep) in enumerate(SYSTEM_TEMPLATE):
                    cur.execute(
                        """INSERT INTO systems(system_id,property_id,system_type,name,depends_on)
                           VALUES(%s,%s,%s,%s,%s) ON CONFLICT (system_id) DO NOTHING""",
                        (ids[i], pid, stype, name, ids[dep] if dep is not None else None))

    generate_systems(load_properties())


seed_properties()
