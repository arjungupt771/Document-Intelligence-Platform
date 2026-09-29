from app.analyst.completeness import CompletenessAnalyzer
from app.analyst.models import AnalysisContext
from app.documents.models import DocumentType
from tests.analyst.conftest import make_document, make_extraction


class TestCompletenessAnalyzer:
    def test_flags_missing_required_fields(self):
        context = AnalysisContext(
            document=make_document(DocumentType.INVOICE),
            extraction=make_extraction({"vendor": None, "invoice_number": "INV-1"}, DocumentType.INVOICE),
        )

        insights = CompletenessAnalyzer().analyze(context)

        assert any(i.title == "Required fields missing" for i in insights)

    def test_flags_low_confidence_fields(self):
        extraction = make_extraction(
            {"vendor": "Acme", "invoice_number": "INV-1", "invoice_date": "2026-01-01", "total": "100"},
            DocumentType.INVOICE,
            field_confidence={"vendor": 0.2},
        )
        context = AnalysisContext(document=make_document(DocumentType.INVOICE), extraction=extraction)

        insights = CompletenessAnalyzer().analyze(context)

        assert any(i.title == "Low-confidence extracted fields" for i in insights)

    def test_no_insights_when_complete_and_confident(self):
        extraction = make_extraction(
            {"vendor": "Acme", "invoice_number": "INV-1", "invoice_date": "2026-01-01", "total": "100"},
            DocumentType.INVOICE,
            field_confidence={"vendor": 0.9},
        )
        context = AnalysisContext(document=make_document(DocumentType.INVOICE), extraction=extraction)

        assert CompletenessAnalyzer().analyze(context) == []