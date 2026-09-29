from decimal import Decimal
from typing import Optional

from app.analyst.base import Analyzer
from app.analyst.models import AnalysisContext, Insight, InsightEvidence, InsightType, Severity
from app.documents.models import DocumentType

TOLERANCE = Decimal("0.01")


class FinancialAnalyzer(Analyzer):
    """Cross-checks arithmetic inside invoice / purchase-order line items."""

    def analyze(self, context: AnalysisContext) -> list[Insight]:
        document_type = context.document.document_type
        if document_type not in (DocumentType.INVOICE, DocumentType.PURCHASE_ORDER):
            return []

        data = context.extraction.data or {}
        items_key = "line_items" if document_type == DocumentType.INVOICE else "items"
        items = data.get(items_key) or []

        subtotal = self._to_decimal(data.get("subtotal"))
        tax = self._to_decimal(data.get("tax"))
        total = self._to_decimal(data.get("total"))
        line_item_total = self._sum_line_items(items)

        evidence = [
            InsightEvidence(
                document_id=str(context.document.id),
                document_type=document_type.value,
                text=(
                    f"{items_key}={items!r}, subtotal={data.get('subtotal')}, "
                    f"tax={data.get('tax')}, total={data.get('total')}"
                ),
                extraction_id=str(context.extraction.id),
            )
        ]

        insights: list[Insight] = []

        if items and line_item_total is not None and subtotal is not None:
            if abs(line_item_total - subtotal) > TOLERANCE:
                insights.append(
                    Insight(
                        type=InsightType.FINANCIAL,
                        severity=Severity.HIGH,
                        title="Line items do not sum to subtotal",
                        description=(
                            f"Line items sum to {line_item_total}, but the extracted subtotal is "
                            f"{subtotal} (difference {abs(line_item_total - subtotal)})."
                        ),
                        confidence=0.9,
                        evidence=evidence,
                    )
                )

        if subtotal is not None and tax is not None and total is not None:
            expected_total = subtotal + tax
            if abs(expected_total - total) > TOLERANCE:
                insights.append(
                    Insight(
                        type=InsightType.FINANCIAL,
                        severity=Severity.HIGH,
                        title="Subtotal plus tax does not match total",
                        description=(
                            f"subtotal ({subtotal}) + tax ({tax}) = {expected_total}, but the "
                            f"extracted total is {total}."
                        ),
                        confidence=0.9,
                        evidence=evidence,
                    )
                )

        if total is not None and total < 0:
            insights.append(
                Insight(
                    type=InsightType.FINANCIAL,
                    severity=Severity.MEDIUM,
                    title="Negative total amount",
                    description=f"The extracted total ({total}) is negative.",
                    confidence=0.8,
                    evidence=evidence,
                )
            )

        if total is not None and not data.get("currency"):
            insights.append(
                Insight(
                    type=InsightType.FINANCIAL,
                    severity=Severity.LOW,
                    title="Missing currency on a monetary document",
                    description="A total amount was extracted but no currency code was found.",
                    confidence=0.7,
                    evidence=evidence,
                )
            )

        return insights

    @staticmethod
    def _to_decimal(value) -> Optional[Decimal]:
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except Exception:
            return None

    @classmethod
    def _sum_line_items(cls, items: list[dict]) -> Optional[Decimal]:
        if not items:
            return None
        totals = [cls._to_decimal(item.get("total")) for item in items]
        if any(t is None for t in totals):
            return None
        return sum(totals, Decimal("0"))