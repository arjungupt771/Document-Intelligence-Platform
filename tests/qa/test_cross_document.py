from app.qa.cross_document import CrossDocumentContext
from app.qa.models import AnswerSource


def test_cross_document_context_preserves_document_boundaries():
    context = CrossDocumentContext(
        query="Compare the invoices.",
        sources=[
            AnswerSource(
                document_id="doc-1",
                document_type="invoice",
                text='{"total_amount": 12000}',
            ),
            AnswerSource(
                document_id="doc-2",
                document_type="invoice",
                text='{"total_amount": 15000}',
            ),
        ],
    )

    text = context.as_text()

    assert "Document ID: doc-1" in text
    assert "Document ID: doc-2" in text
    assert '{"total_amount": 12000}' in text
    assert '{"total_amount": 15000}' in text


def test_document_ids_are_unique_and_ordered():
    context = CrossDocumentContext(
        query="Compare the invoices.",
        sources=[
            AnswerSource(
                document_id="doc-1",
                document_type="invoice",
                text="first",
            ),
            AnswerSource(
                document_id="doc-1",
                document_type="invoice",
                text="second",
            ),
            AnswerSource(
                document_id="doc-2",
                document_type="invoice",
                text="third",
            ),
        ],
    )

    assert context.document_ids == ["doc-1", "doc-2"]


def test_empty_cross_document_context():
    context = CrossDocumentContext(
        query="Compare the documents.",
    )

    assert context.is_empty is True
    assert context.document_ids == []
    assert context.as_text() == "No evidence was retrieved for this question."