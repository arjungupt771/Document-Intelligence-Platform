from decimal import Decimal
from typing import Optional

from app.analyst.base import ComparativeAnalyzer
from app.analyst.models import AnalysisContext, Insight, InsightEvidence, InsightType, Severity
from app.documents.models import DocumentType

TOLERANCE = Decimal("0.01")


class InvoicePurchaseOrderMatcher(ComparativeAnalyzer):
    """Three-way-match style comparison between an invoice and a purchase order."""

    def compare(self, context_a: AnalysisContext, context_b: AnalysisContext) -> list[Insight]:
        invoice_ctx, po_ctx = self._order(context_a, context_b)
        if invoice_ctx is None:
            return []

        invoice = invoice_ctx.extraction.data or {}
        po = po_ctx.extraction.data or {}
        document_ids = [str(invoice_ctx.document.id), str(po_ctx.document.id)]
        evidence = [
            InsightEvidence(
                document_id=str(invoice_ctx.document.id),
                document_type=DocumentType.INVOICE.value,
                text=f"vendor={invoice.get('vendor')}, total={invoice.get('total')}",
                extraction_id=str(invoice_ctx.extraction.id),
            ),
            InsightEvidence(
                document_id=str(po_ctx.document.id),
                document_type=DocumentType.PURCHASE_ORDER.value,
                text=f"supplier={po.get('supplier')}, total={po.get('total')}",
                extraction_id=str(po_ctx.extraction.id),
            ),
        ]

        insights: list[Insight] = []

        vendor = self._normalize(invoice.get("vendor"))
        supplier = self._normalize(po.get("supplier"))
        if vendor and supplier and vendor != supplier:
            insights.append(
                Insight(
                    type=InsightType.CROSS_DOCUMENT,
                    severity=Severity.HIGH,
                    title="Invoice vendor does not match PO supplier",
                    description=(
                        f"Invoice vendor is '{invoice.get('vendor')}' but the matched PO supplier "
                        f"is '{po.get('supplier')}'."
                    ),
                    confidence=0.8,
                    evidence=evidence,
                    document_ids=document_ids,
                )
            )

        invoice_total = self._to_decimal(invoice.get("total"))
        po_total = self._to_decimal(po.get("total"))
        if invoice_total is not None and po_total is not None and abs(invoice_total - po_total) > TOLERANCE:
            insights.append(
                Insight(
                    type=InsightType.CROSS_DOCUMENT,
                    severity=Severity.HIGH,
                    title="Invoice total does not match PO total",
                    description=f"Invoice total is {invoice_total}; matched PO total is {po_total}.",
                    confidence=0.85,
                    evidence=evidence,
                    document_ids=document_ids,
                )
            )

        return insights

    @staticmethod
    def _order(context_a: AnalysisContext, context_b: AnalysisContext):
        by_type = {ctx.document.document_type: ctx for ctx in (context_a, context_b)}
        invoice_ctx = by_type.get(DocumentType.INVOICE)
        po_ctx = by_type.get(DocumentType.PURCHASE_ORDER)
        if invoice_ctx is None or po_ctx is None:
            return None, None
        return invoice_ctx, po_ctx

    @staticmethod
    def _normalize(value: Optional[str]) -> Optional[str]:
        return value.strip().lower() if isinstance(value, str) else None

    @staticmethod
    def _to_decimal(value) -> Optional[Decimal]:
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except Exception:
            return None