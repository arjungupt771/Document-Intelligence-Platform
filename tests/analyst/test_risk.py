from datetime import date, timedelta

from app.analyst.models import AnalysisContext
from app.analyst.risk import RiskAnalyzer
from app.documents.models import DocumentType
from tests.analyst.conftest import make_document, make_extraction


class TestRiskAnalyzer:
    def test_flags_overdue_invoice(self):
        past_due = (date.today() - timedelta(days=5)).isoformat()
        context = AnalysisContext(
            document=make_document(DocumentType.INVOICE),
            extraction=make_extraction({"due_date": past_due}, DocumentType.INVOICE),
        )

        titles = [i.title for i in RiskAnalyzer().analyze(context)]

        assert "Invoice past due date" in titles

    def test_flags_low_extraction_confidence(self):
        context = AnalysisContext(
            document=make_document(DocumentType.CONTRACT),
            extraction=make_extraction({}, DocumentType.CONTRACT, confidence=0.3),
        )

        titles = [i.title for i in RiskAnalyzer().analyze(context)]

        assert "Low overall extraction confidence" in titles

    def test_flags_missing_termination_date(self):
        context = AnalysisContext(
            document=make_document(DocumentType.CONTRACT),
            extraction=make_extraction(
                {"effective_date": "2026-01-01", "termination_date": None},
                DocumentType.CONTRACT,
                confidence=0.9,
            ),
        )

        titles = [i.title for i in RiskAnalyzer().analyze(context)]

        assert "No termination date on file" in titles

    def test_flags_auto_renewal_clause(self):
        context = AnalysisContext(
            document=make_document(DocumentType.CONTRACT),
            extraction=make_extraction(
                {"renewal_terms": "This agreement will automatically renew annually."},
                DocumentType.CONTRACT,
                confidence=0.9,
            ),
        )

        titles = [i.title for i in RiskAnalyzer().analyze(context)]

        assert "Auto-renewal clause present" in titles