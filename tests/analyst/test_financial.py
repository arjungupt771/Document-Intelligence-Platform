from app.analyst.financial import FinancialAnalyzer
from app.analyst.models import AnalysisContext
from app.documents.models import DocumentType
from tests.analyst.conftest import make_document, make_extraction


class TestFinancialAnalyzer:
    def test_flags_line_item_subtotal_mismatch(self):
        context = AnalysisContext(
            document=make_document(DocumentType.INVOICE),
            extraction=make_extraction(
                {
                    "line_items": [{"description": "A", "total": "100.00"}],
                    "subtotal": "150.00",
                    "tax": "0",
                    "total": "150.00",
                    "currency": "USD",
                },
                DocumentType.INVOICE,
            ),
        )

        titles = [i.title for i in FinancialAnalyzer().analyze(context)]

        assert "Line items do not sum to subtotal" in titles

    def test_flags_subtotal_plus_tax_mismatch(self):
        context = AnalysisContext(
            document=make_document(DocumentType.INVOICE),
            extraction=make_extraction(
                {
                    "line_items": [{"description": "A", "total": "100.00"}],
                    "subtotal": "100.00",
                    "tax": "10.00",
                    "total": "200.00",
                    "currency": "USD",
                },
                DocumentType.INVOICE,
            ),
        )

        titles = [i.title for i in FinancialAnalyzer().analyze(context)]

        assert "Subtotal plus tax does not match total" in titles

    def test_no_insights_when_consistent(self):
        context = AnalysisContext(
            document=make_document(DocumentType.INVOICE),
            extraction=make_extraction(
                {
                    "line_items": [{"description": "A", "total": "100.00"}],
                    "subtotal": "100.00",
                    "tax": "10.00",
                    "total": "110.00",
                    "currency": "USD",
                },
                DocumentType.INVOICE,
            ),
        )

        assert FinancialAnalyzer().analyze(context) == []

    def test_ignores_non_financial_document_types(self):
        context = AnalysisContext(
            document=make_document(DocumentType.CONTRACT),
            extraction=make_extraction({}, DocumentType.CONTRACT),
        )

        assert FinancialAnalyzer().analyze(context) == []