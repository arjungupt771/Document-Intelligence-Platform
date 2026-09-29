"""Loads a small, realistic demo data set through the PUBLIC API (exactly what the
frontend does): generate sample PDFs -> upload -> process -> analyze.

Run inside the api container (has httpx + pymupdf, and API_AUTH_KEY in its env):

    docker compose exec api python scripts/demo_seed.py

Or from your machine (needs `pip install httpx pymupdf`):

    API_BASE=http://localhost:8000 API_AUTH_KEY=<your key> python scripts/demo_seed.py

Safe to re-run: duplicate uploads (same content) are detected by the API and skipped.
"""
import os
import sys
import time

import httpx
import pymupdf

API_BASE = os.environ.get("API_BASE", "http://localhost:8000").rstrip("/")
API_KEY = os.environ.get("API_AUTH_KEY", "")

INVOICES = [
    # (number, vendor, date, due, subtotal, tax, description)
    ("INV-2026-001", "Acme Industrial Supplies Ltd", "2026-08-03", "2026-09-02", "4,200.00", "336.00", "Hydraulic fittings and seals"),
    ("INV-2026-002", "Acme Industrial Supplies Ltd", "2026-08-10", "2026-09-09", "4,650.00", "372.00", "Steel brackets, bulk order"),
    ("INV-2026-003", "Northwind Logistics Inc", "2026-08-17", "2026-09-16", "3,980.00", "318.40", "Freight and warehousing, August"),
    ("INV-2026-004", "Northwind Logistics Inc", "2026-08-24", "2026-09-23", "4,400.00", "352.00", "Freight and warehousing, week 4"),
    # Deliberate outlier -> the analyst should flag this one as anomalous.
    ("INV-2026-005", "Acme Industrial Supplies Ltd", "2026-09-01", "2026-09-15", "48,500.00", "3,880.00", "Emergency machinery replacement"),
]


def _pdf(lines: list[str]) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    y = 72
    for line in lines:
        page.insert_text((72, y), line, fontsize=11)
        y += 18
    data = doc.tobytes()
    doc.close()
    return data


def _money(text: str) -> float:
    return float(text.replace(",", ""))


def invoice_pdf(number, vendor, date, due, subtotal, tax, description) -> bytes:
    total = f"{_money(subtotal) + _money(tax):,.2f}"
    return _pdf([
        "INVOICE",
        f"Invoice Number: {number}",
        f"Invoice Date: {date}",
        f"Due Date: {due}",
        f"From: {vendor}",
        "Bill To: Globex Manufacturing Corp",
        "",
        f"Description: {description}",
        "",
        f"Subtotal: ${subtotal}",
        f"Tax: ${tax}",
        f"Total Due: ${total}",
        "",
        "Payment terms: Net 30. Remit to the vendor account listed on file.",
    ])


def purchase_order_pdf() -> bytes:
    return _pdf([
        "PURCHASE ORDER",
        "PO Number: PO-7781",
        "Order Date: 2026-07-28",
        "Buyer: Globex Manufacturing Corp",
        "Supplier: Acme Industrial Supplies Ltd",
        "Ship To: Globex Plant 2, 14 Foundry Road",
        "",
        "Items: Hydraulic fittings and seals, steel brackets",
        "Order total: $9,000.00",
    ])


def main() -> None:
    if not API_KEY:
        sys.exit("Set API_AUTH_KEY (the same value as in your .env).")

    auth = {"Authorization": f"Bearer {API_KEY}"}
    client = httpx.Client(base_url=API_BASE, headers=auth, timeout=600)

    print(f"Waiting for the API at {API_BASE} ...")
    for _ in range(30):
        try:
            if client.get("/health/ready").status_code == 200:
                break
        except httpx.HTTPError:
            pass
        time.sleep(3)
    else:
        sys.exit("API did not become ready. Check `docker compose ps` and `docker compose logs api`.")

    files = [(f"{i[0]}.pdf", invoice_pdf(*i)) for i in INVOICES]
    files.append(("PO-7781.pdf", purchase_order_pdf()))

    document_ids: dict[str, str] = {}
    for name, content in files:
        r = client.post("/documents/", files={"file": (name, content, "application/pdf")})
        if r.status_code == 201:
            document_ids[name] = r.json()["document_id"]
            print(f"  uploaded   {name}")
        elif r.status_code == 409:
            print(f"  skipped    {name} (already uploaded)")
        else:
            sys.exit(f"Upload of {name} failed: HTTP {r.status_code} {r.text}")

    for name, doc_id in document_ids.items():
        print(f"  processing {name} (the first one loads the embedding model - be patient) ...")
        r = client.post(f"/documents/{doc_id}/process")
        if r.status_code != 200:
            sys.exit(f"Processing {name} failed: HTTP {r.status_code} {r.text}")
        body = r.json()
        print(f"             -> {body['document_type']}, {body['chunks_indexed']} chunks indexed")

    outlier = document_ids.get("INV-2026-005.pdf")
    if outlier:
        r = client.post(f"/analyst/documents/{outlier}/analyze")
        print(f"  analyzed   INV-2026-005.pdf -> {len(r.json()) if r.status_code == 200 else 'failed'} insight(s)")

    print("\nDemo data is loaded. Open the frontend and try these questions on the Ask page:")
    print("  - What is the total amount due on invoice INV-2026-002?")
    print("  - Who is the vendor on invoice INV-2026-003?")
    print("  - When is invoice INV-2026-001 due?")
    print("  - What is the invoice total for the emergency machinery replacement?")


if __name__ == "__main__":
    main()