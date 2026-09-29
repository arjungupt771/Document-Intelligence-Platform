import re
from typing import Optional

from app.extraction.base import ExtractionResult, Extractor
from app.extraction.normalization import normalize_amount, normalize_currency, normalize_date
from app.extraction.schemas import InvoiceSchema, LineItem
from app.parsing.models import ParsedDocument, TableBlock

_FIELD_PATTERNS: dict[str, re.Pattern] = {
    "invoice_number": re.compile(
        r"invoice\s*(?:no|number|#)\.?\s*[:\-]?\s*([A-Za-z0-9\-]+)", re.IGNORECASE
    ),
    "invoice_date": re.compile(
        r"invoice\s*date\s*[:\-]?\s*([A-Za-z0-9,\s/\-]+?)(?=\n|$)", re.IGNORECASE
    ),
    "due_date": re.compile(
        r"due\s*date\s*[:\-]?\s*([A-Za-z0-9,\s/\-]+?)(?=\n|$)", re.IGNORECASE
    ),
    "vendor": re.compile(
        r"(?:^|\n)\s*(?:from|vendor|remit\s*to)\s*[:\-]?\s*(.+?)(?=\n|$)", re.IGNORECASE
    ),
    "subtotal": re.compile(r"subtotal\s*[:\-]?\s*\$?([\d,]+\.?\d*)", re.IGNORECASE),
    "tax": re.compile(r"\btax\s*[:\-]?\s*\$?([\d,]+\.?\d*)", re.IGNORECASE),
    "total": re.compile(
    r"\btotal[ \t]*(?:paid|due)?[ \t]*(?:\([A-Z]{3}\))?[ \t]*[:\-][ \t]*(?:\n[ \t]*)?\$?([\d,]+\.?\d*)",
    re.IGNORECASE,
),
}

_LINE_ITEM_HEADER_HINTS = ("desc", "item")


class InvoiceExtractor(Extractor[InvoiceSchema]):
    """
    Baseline extractor for invoices: regex over the document's free text
    for scalar fields, plus table detection for line_items[]. This is
    the extraction-side equivalent of the rule-based classifier -- a
    simple, explainable baseline to benchmark ML/LLM extractors against.
    """

    def extract(self, document: ParsedDocument) -> ExtractionResult[InvoiceSchema]:
        text = document.text

        raw_fields: dict[str, Optional[str]] = {
            field_name: self._first_match(pattern, text)
            for field_name, pattern in _FIELD_PATTERNS.items()
        }
        currency = normalize_currency(text)
        line_items = self._extract_line_items(document)

        schema = InvoiceSchema(
            vendor=raw_fields["vendor"],
            invoice_number=raw_fields["invoice_number"],
            invoice_date=normalize_date(raw_fields["invoice_date"]),
            due_date=normalize_date(raw_fields["due_date"]),
            currency=currency,
            subtotal=normalize_amount(raw_fields["subtotal"]),
            tax=normalize_amount(raw_fields["tax"]),
            total=normalize_amount(raw_fields["total"]),
            line_items=line_items,
        )

        field_confidence = self._field_confidence(schema)
        overall_confidence = sum(field_confidence.values()) / len(field_confidence)

        return ExtractionResult(
            data=schema,
            confidence=overall_confidence,
            field_confidence=field_confidence,
        )

    @staticmethod
    def _first_match(pattern: re.Pattern, text: str) -> Optional[str]:
        match = pattern.search(text)
        return match.group(1).strip() if match else None

    @staticmethod
    def _field_confidence(schema: InvoiceSchema) -> dict[str, float]:
        scalar_fields = (
            "vendor",
            "invoice_number",
            "invoice_date",
            "due_date",
            "currency",
            "subtotal",
            "tax",
            "total",
        )
        confidence = {
            field_name: (1.0 if getattr(schema, field_name) is not None else 0.0)
            for field_name in scalar_fields
        }
        confidence["line_items"] = 1.0 if schema.line_items else 0.0
        return confidence

    @staticmethod
    def _extract_line_items(document: ParsedDocument) -> list[LineItem]:
        line_items: list[LineItem] = []

        for table in document.tables:
            if not InvoiceExtractor._looks_like_line_item_table(table):
                continue

            rows: dict[int, dict[int, str]] = {}
            for cell in table.cells:
                rows.setdefault(cell.row, {})[cell.column] = cell.text

            for row_index in sorted(rows):
                if row_index == 0:  # header row
                    continue

                row = rows[row_index]
                description = row.get(0, "").strip()
                if not description:
                    continue

                line_items.append(
                    LineItem(
                        description=description,
                        quantity=normalize_amount(row.get(1)),
                        unit_price=normalize_amount(row.get(2)),
                        total=normalize_amount(row.get(3)),
                    )
                )

        return line_items

    @staticmethod
    def _looks_like_line_item_table(table: TableBlock) -> bool:
        header_cells = [cell.text.lower() for cell in table.cells if cell.row == 0]
        return any(
            hint in header_cell for header_cell in header_cells for hint in _LINE_ITEM_HEADER_HINTS
        )