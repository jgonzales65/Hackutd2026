"""Generates SAMPLE (fictional) deeds, liens and a zoning notice as PDFs.
All names, amounts and parcel numbers are made up for the demo.
    python3 data/make_sample_pdfs.py
"""
import os

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

OUT = os.path.join(os.path.dirname(__file__), "documents")
os.makedirs(OUT, exist_ok=True)

DOCS = {
    "deed_BX-001.pdf": [
        "WARRANTY DEED  (SAMPLE - FICTIONAL)",
        "Bexar County, Texas",
        "Property ID: BX-001",
        "Parcel No: 100234-0010-0001",
        "Grantor: Alamo Holdings LLC",
        "Grantee: Riverbend Capital Partners LP",
        "Sale Price: $84,500,000",
        "Recording Date: 03/14/2022",
        "Document No: 2022-0045123",
        "Legal Description: Lot 4, Block 12, NCB 118, City of San Antonio",
    ],
    "deed_BX-004.pdf": [
        "SPECIAL WARRANTY DEED  (SAMPLE - FICTIONAL)",
        "Bexar County, Texas",
        "Property ID: BX-004",
        "Parcel No: 220871-0000-0020",
        "Grantor: Port Logistics Trust",
        "Grantee: Lone Star Compute Inc",
        "Sale Price: $118,000,000",
        "Recording Date: 08/02/2023",
        "Document No: 2023-0098812",
        "Legal Description: Tract 2, Survey 45, Bexar County",
    ],
    "lien_BX-002.pdf": [
        "NOTICE OF MECHANIC'S LIEN  (SAMPLE - FICTIONAL)",
        "Bexar County, Texas",
        "Property ID: BX-002",
        "Parcel No: 100456-0020-0005",
        "Lien Claimant: Hill Country Roofing Co",
        "Property Owner: Riverwalk Retail Group LLC",
        "Lien Amount: $412,750.00",
        "Filing Date: 06/21/2026",
        "Document No: 2026-0071544",
        "Status: ACTIVE",
    ],
    "lien_BX-006.pdf": [
        "NOTICE OF TAX LIEN  (SAMPLE - FICTIONAL)",
        "Bexar County, Texas",
        "Property ID: BX-006",
        "Parcel No: 330912-0000-0007",
        "Lien Claimant: Bexar County Tax Office",
        "Property Owner: Southside Industrial Holdings",
        "Lien Amount: $58,300.00",
        "Filing Date: 01/09/2026",
        "Document No: 2026-0003391",
        "Status: ACTIVE",
    ],
    "zoning_BX-003.pdf": [
        "NOTICE OF ZONING CHANGE  (SAMPLE - FICTIONAL)",
        "City of San Antonio Development Services",
        "Property ID: BX-003",
        "Parcel No: 140778-0010-0003",
        "Current Zoning: C-2",
        "Proposed Zoning: MXD",
        "Hearing Date: 12/04/2026",
        "Case No: Z-2026-10700123",
        "Applicant: Medical Center Office Partners",
    ],
}

for name, lines in DOCS.items():
    c = canvas.Canvas(os.path.join(OUT, name), pagesize=letter)
    y = 740
    for i, line in enumerate(lines):
        c.setFont("Helvetica-Bold" if i == 0 else "Helvetica", 14 if i == 0 else 11)
        c.drawString(72, y, line)
        y -= 26 if i == 0 else 20
    c.save()
print(f"wrote {len(DOCS)} PDFs to {OUT}")
