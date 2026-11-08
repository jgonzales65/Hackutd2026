"""DAG 4: parse PDF deeds, liens and zoning notices into the documents table.
Drop new PDFs into data/documents/ and trigger the DAG (it also runs hourly)."""
import json
import os
from datetime import datetime

from airflow.decorators import dag, task

from common import conn

DOC_DIR = os.environ.get("DOC_DIR", "/opt/airflow/data/documents")


@dag(dag_id="parse_documents", start_date=datetime(2026, 11, 1), schedule="@hourly", catchup=False,
     max_active_runs=1, tags=["bexar", "documents"])
def parse_documents():
    @task
    def find_new_pdfs():
        with conn() as c, c.cursor() as cur:
            cur.execute("SELECT source_file FROM documents")
            done = {r[0] for r in cur.fetchall()}
        return sorted(f for f in os.listdir(DOC_DIR) if f.lower().endswith(".pdf") and f not in done)

    @task
    def parse_and_load(filename):
        from doc_parser import parse_pdf  # imported here so DAG parsing stays fast

        result = parse_pdf(os.path.join(DOC_DIR, filename))
        pid = result["fields"].get("property_id")
        with conn() as c, c.cursor() as cur:
            cur.execute("SELECT 1 FROM properties WHERE property_id=%s", (pid,))
            if cur.fetchone() is None:
                pid = None  # unknown property: still store it, unlinked, so nothing is lost
            cur.execute(
                "INSERT INTO documents(property_id,doc_type,parsed,source_file) VALUES(%s,%s,%s,%s)",
                (pid, result["doc_type"], json.dumps(result), filename))
        return {"file": filename, "type": result["doc_type"], "confidence": result["confidence"]}

    parse_and_load.expand(filename=find_new_pdfs())


parse_documents()