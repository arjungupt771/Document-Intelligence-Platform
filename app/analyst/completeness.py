from app.analyst.base import Analyzer
from app.analyst.models import AnalysisContext, Insight, InsightEvidence, InsightType, Severity
from app.documents.models import DocumentType

REQUIRED_FIELDS: dict[DocumentType, list[str]] = {
    DocumentType.INVOICE: ["vendor", "invoice_number", "invoice_date", "total"],
    DocumentType.PURCHASE_ORDER: ["buyer", "supplier", "po_number", "total"],
    DocumentType.CONTRACT: ["parties", "effective_date"],
}

LOW_CONFIDENCE_THRESHOLD = 0.5


class CompletenessAnalyzer(Analyzer):
    """Flags required fields the extractor could not fill, and fields it filled with low confidence."""

    def analyze(self, context: AnalysisContext) -> list[Insight]:
        required = REQUIRED_FIELDS.get(context.document.document_type, [])
        data = context.extraction.data or {}
        field_confidence = context.extraction.field_confidence or {}
        insights: list[Insight] = []

        missing = [name for name in required if self._is_empty(data.get(name))]
        if missing:
            insights.append(
                Insight(
                    type=InsightType.COMPLETENESS,
                    severity=Severity.HIGH if len(missing) > 1 else Severity.MEDIUM,
                    title="Required fields missing",
                    description=f"The following required fields could not be extracted: {', '.join(missing)}.",
                    confidence=0.85,
                    evidence=[
                        InsightEvidence(
                            document_id=str(context.document.id),
                            document_type=context.document.document_type.value,
                            text=f"missing fields: {missing}",
                            extraction_id=str(context.extraction.id),
                        )
                    ],
                    metadata={"missing_fields": missing},
                )
            )

        low_confidence_fields = [
            name
            for name, conf in field_confidence.items()
            if conf is not None and conf < LOW_CONFIDENCE_THRESHOLD and not self._is_empty(data.get(name))
        ]
        if low_confidence_fields:
            insights.append(
                Insight(
                    type=InsightType.COMPLETENESS,
                    severity=Severity.LOW,
                    title="Low-confidence extracted fields",
                    description=(
                        "These fields were extracted but with low model confidence and should be "
                        f"spot-checked: {', '.join(low_confidence_fields)}."
                    ),
                    confidence=0.6,
                    evidence=[
                        InsightEvidence(
                            document_id=str(context.document.id),
                            document_type=context.document.document_type.value,
                            text=f"field_confidence: {field_confidence}",
                            extraction_id=str(context.extraction.id),
                        )
                    ],
                    metadata={"low_confidence_fields": low_confidence_fields},
                )
            )

        return insights

    @staticmethod
    def _is_empty(value) -> bool:
        if value is None:
            return True
        if isinstance(value, (list, dict, str)) and len(value) == 0:
            return True
        return False