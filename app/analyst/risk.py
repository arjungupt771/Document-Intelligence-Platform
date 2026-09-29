from datetime import date, datetime

from app.analyst.base import Analyzer
from app.analyst.models import AnalysisContext, Insight, InsightEvidence, InsightType, Severity
from app.documents.models import DocumentType

LOW_EXTRACTION_CONFIDENCE = 0.5
AUTO_RENEWAL_KEYWORDS = ("automatically renew", "auto-renew", "auto renew")


class RiskAnalyzer(Analyzer):
    def analyze(self, context: AnalysisContext) -> list[Insight]:
        insights: list[Insight] = []
        data = context.extraction.data or {}
        document_type = context.document.document_type

        if (
            context.extraction.confidence is not None
            and context.extraction.confidence < LOW_EXTRACTION_CONFIDENCE
        ):
            insights.append(self._low_confidence_insight(context))

        if document_type == DocumentType.INVOICE:
            insights.extend(self._invoice_risks(context, data))
        elif document_type == DocumentType.CONTRACT:
            insights.extend(self._contract_risks(context, data))

        return insights

    def _low_confidence_insight(self, context: AnalysisContext) -> Insight:
        return Insight(
            type=InsightType.RISK,
            severity=Severity.MEDIUM,
            title="Low overall extraction confidence",
            description=(
                f"This document's extraction confidence is {context.extraction.confidence:.2f}, "
                f"below the {LOW_EXTRACTION_CONFIDENCE} review threshold. Manual review is "
                "recommended before relying on its extracted fields."
            ),
            confidence=0.75,
            evidence=[
                InsightEvidence(
                    document_id=str(context.document.id),
                    document_type=context.document.document_type.value,
                    text=f"extraction confidence = {context.extraction.confidence}",
                    extraction_id=str(context.extraction.id),
                )
            ],
        )

    def _invoice_risks(self, context: AnalysisContext, data: dict) -> list[Insight]:
        due = self._parse_date(data.get("due_date"))
        if due is None or due >= date.today():
            return []
        return [
            Insight(
                type=InsightType.RISK,
                severity=Severity.HIGH,
                title="Invoice past due date",
                description=f"The invoice due date ({due.isoformat()}) has already passed.",
                confidence=0.85,
                evidence=[
                    InsightEvidence(
                        document_id=str(context.document.id),
                        document_type=context.document.document_type.value,
                        text=f"due_date={data.get('due_date')}",
                        field_path="due_date",
                        extraction_id=str(context.extraction.id),
                    )
                ],
            )
        ]

    def _contract_risks(self, context: AnalysisContext, data: dict) -> list[Insight]:
        insights = []

        if data.get("effective_date") and not data.get("termination_date"):
            insights.append(
                Insight(
                    type=InsightType.RISK,
                    severity=Severity.MEDIUM,
                    title="No termination date on file",
                    description=(
                        "This contract has an effective date but no extracted termination date -- "
                        "confirm whether it is open-ended or the field was missed."
                    ),
                    confidence=0.6,
                    evidence=[
                        InsightEvidence(
                            document_id=str(context.document.id),
                            document_type=context.document.document_type.value,
                            text=f"effective_date={data.get('effective_date')}, termination_date=None",
                            extraction_id=str(context.extraction.id),
                        )
                    ],
                )
            )

        renewal_terms = (data.get("renewal_terms") or "").lower()
        if any(keyword in renewal_terms for keyword in AUTO_RENEWAL_KEYWORDS):
            insights.append(
                Insight(
                    type=InsightType.RISK,
                    severity=Severity.LOW,
                    title="Auto-renewal clause present",
                    description="This contract appears to auto-renew; confirm the notice period required to opt out.",
                    confidence=0.7,
                    evidence=[
                        InsightEvidence(
                            document_id=str(context.document.id),
                            document_type=context.document.document_type.value,
                            text=data.get("renewal_terms", ""),
                            field_path="renewal_terms",
                            extraction_id=str(context.extraction.id),
                        )
                    ],
                )
            )

        return insights

    @staticmethod
    def _parse_date(value) -> date | None:
        if value is None:
            return None
        if isinstance(value, date):
            return value
        try:
            return datetime.fromisoformat(str(value)).date()
        except ValueError:
            return None