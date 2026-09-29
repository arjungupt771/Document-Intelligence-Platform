import re
from typing import Optional

from app.extraction.base import ExtractionResult, Extractor
from app.extraction.normalization import normalize_amount, normalize_currency, normalize_date
from app.extraction.schemas import PurchaseOrderItem, PurchaseOrderSchema
from app.parsing.models import ParsedDocument, TableBlock

_FIELD_PATTERNS: dict[str, re.Pattern] = {
    "po_number": re.compile(
        r"p\.?o\.?\s*(?:no|number|#)\.?\s*[:\-]?\s*([A-Za-z0-9\-]+)", re.IGNORECASE
    ),
    "order_date": re.compile(
        r"order\s*date\s*[:\-]?\s*([A-Za-z0-9,\s/\-]+?)(?=\n|$)", re.IGNORECASE
    ),
    "buyer": re.compile(r"(?:^|\n)\s*buyer\s*[:\-]?\s*(.+?)(?=\n|$)", re.IGNORECASE),
    "supplier": re.compile(r"(?:^|\n)\s*supplier\s*[:\-]?\s*(.+?)(?=\n|$)", re.IGNORECASE),
    "total": re.compile(r"\btotal\s*[:\-]?\s*\$?([\d,]+\.?\d*)", re.IGNORECASE),
}

_ITEM_HEADER_HINTS = ("desc", "item")


class PurchaseOrderExtractor(Extractor[PurchaseOrderSchema]):
    """
    Baseline extractor for purchase orders: regex over free text for
    scalar fields (buyer, supplier, po_number, order_date, total), plus
    table detection for items[].
    """

    def extract(self, document: ParsedDocument) -> ExtractionResult[PurchaseOrderSchema]:
        text = document.text

        raw_fields: dict[str, Optional[str]] = {
            field_name: self._first_match(pattern, text)
            for field_name, pattern in _FIELD_PATTERNS.items()
        }
        currency = normalize_currency(text)
        items = self._extract_items(document)

        schema = PurchaseOrderSchema(
            buyer=raw_fields["buyer"],
            supplier=raw_fields["supplier"],
            po_number=raw_fields["po_number"],
            order_date=normalize_date(raw_fields["order_date"]),
            items=items,
            currency=currency,
            total=normalize_amount(raw_fields["total"]),
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
    def _field_confidence(schema: PurchaseOrderSchema) -> dict[str, float]:
        scalar_fields = ("buyer", "supplier", "po_number", "order_date", "currency", "total")
        confidence = {
            field_name: (1.0 if getattr(schema, field_name) is not None else 0.0)
            for field_name in scalar_fields
        }
        confidence["items"] = 1.0 if schema.items else 0.0
        return confidence

    @staticmethod
    def _extract_items(document: ParsedDocument) -> list[PurchaseOrderItem]:
        items: list[PurchaseOrderItem] = []

        for table in document.tables:
            if not PurchaseOrderExtractor._looks_like_item_table(table):
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

                items.append(
                    PurchaseOrderItem(
                        description=description,
                        quantity=normalize_amount(row.get(1)),
                        unit_price=normalize_amount(row.get(2)),
                        total=normalize_amount(row.get(3)),
                    )
                )

        return items

    @staticmethod
    def _looks_like_item_table(table: TableBlock) -> bool:
        header_cells = [cell.text.lower() for cell in table.cells if cell.row == 0]
        return any(
            hint in header_cell for header_cell in header_cells for hint in _ITEM_HEADER_HINTS
        )