"""PDF -> structured JSON. Text extraction with pdfplumber, then document-type
classification and field extraction with regexes.

Swap `extract_text` for Unstructured.io / Amazon Textract to handle scanned or messy PDFs;
everything after it stays the same.
"""
import re
from datetime import datetime

import pdfplumber

FIELDS = {
    "property_id": r"Property ID:\s*(\S+)",
    "parcel_no": r"Parcel No:\s*([\d\-]+)",
    "document_no": r"Document No:\s*(\S+)",
    "grantor": r"Grantor:\s*(.+)",
    "grantee": r"Grantee:\s*(.+)",
    "sale_price": r"Sale Price:\s*\$([\d,\.]+)",
    "recording_date": r"Recording Date:\s*([\d/]+)",
    "lien_claimant": r"Lien Claimant:\s*(.+)",
    "property_owner": r"Property Owner:\s*(.+)",
    "lien_amount": r"Lien Amount:\s*\$([\d,\.]+)",
    "filing_date": r"Filing Date:\s*([\d/]+)",
    "status": r"Status:\s*(\w+)",
    "current_zoning": r"Current Zoning:\s*(\S+)",
    "proposed_zoning": r"Proposed Zoning:\s*(\S+)",
    "hearing_date": r"Hearing Date:\s*([\d/]+)",
    "case_no": r"Case No:\s*(\S+)",
    "applicant": r"Applicant:\s*(.+)",
    "legal_description": r"Legal Description:\s*(.+)",
}
MONEY = {"sale_price", "lien_amount"}
DATES = {"recording_date", "filing_date", "hearing_date"}


def extract_text(path):
    with pdfplumber.open(path) as pdf:
        return "\n".join((p.extract_text() or "") for p in pdf.pages)


def classify(text):
    t = text.upper()
    if "LIEN" in t:
        return "lien"
    if "ZONING" in t:
        return "zoning"
    if "DEED" in t:
        return "deed"
    return "unknown"


def parse_text(text):
    out = {}
    for key, pat in FIELDS.items():
        m = re.search(pat, text)
        if not m:
            continue
        v = m.group(1).strip()
        if key in MONEY:
            v = float(v.replace(",", ""))
        elif key in DATES:
            v = datetime.strptime(v, "%m/%d/%Y").date().isoformat()
        out[key] = v
    return out


def parse_pdf(path):
    text = extract_text(path)
    fields = parse_text(text)
    doc_type = classify(text)
    # Confidence: share of the type's expected fields that were found.
    expected = {"deed": 7, "lien": 8, "zoning": 6}.get(doc_type, 1)
    return {"doc_type": doc_type, "fields": fields,
            "confidence": round(min(len(fields) / expected, 1.0), 2)}
