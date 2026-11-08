"""DAG 3: pull active NWS severe-weather alerts for Texas every 15 minutes."""
from datetime import datetime

from airflow.decorators import dag, task

import connectors
from common import conn


@dag(dag_id="weather_alerts", start_date=datetime(2026, 11, 1), schedule="*/15 * * * *", catchup=False,
     max_active_runs=1, tags=["bexar", "weather"])
def weather_alerts():
    @task
    def fetch_and_store():
        alerts = connectors.nws_alerts("TX")
        with conn() as c, c.cursor() as cur:
            for a in alerts:
                cur.execute(
                    """INSERT INTO alerts(alert_id,state,severity,event,headline,area_desc,sent_at)
                       VALUES(%(alert_id)s,%(state)s,%(severity)s,%(event)s,%(headline)s,%(area_desc)s,%(sent_at)s)
                       ON CONFLICT (alert_id) DO UPDATE SET severity=EXCLUDED.severity, fetched_at=now()""", a)
        return len(alerts)

    fetch_and_store()


weather_alerts()
