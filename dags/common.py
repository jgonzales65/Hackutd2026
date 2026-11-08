"""Shared helpers: warehouse connection + resilient HTTP."""
import os
import time

import psycopg2
import requests

DSN = os.environ.get("WAREHOUSE_DSN", "postgresql://cascade:cascade@postgres:5432/cascade")
UA = {"User-Agent": "cascade-hackathon-demo"}


def conn():
    return psycopg2.connect(DSN)


def get_json(url, params=None, retries=3, timeout=30):
    """GET with retries. Returns parsed JSON or raises after the last attempt."""
    last = None
    for i in range(retries):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 * (i + 1))
    raise last
