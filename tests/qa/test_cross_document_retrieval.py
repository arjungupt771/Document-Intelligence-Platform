from app.qa.cross_document_retrieval import CrossDocumentRetrievalAdapter
from app.retrieval.models import RetrievedChunk, RetrievalResult


def test_converts_retrieval_result_to_cross_document_context():
    result = RetrievalResult(
        query="Compare the invoices.",
        chunks=[
            RetrievedChunk(
                document_id="doc-1",
                document_type="invoice",
                chunk_index=0,
                page_number=1,
                text="Invoice total is 12000.",
                score=0.91,
            ),
            RetrievedChunk(
                document_id="doc-2",
                document_type="invoice",
                chunk_index=0,
                page_number=1,
                text="Invoice total is 15000.",
                score=0.89,
            ),
        ],
    )

    adapter = CrossDocumentRetrievalAdapter()

    context = adapter.from_retrieval_result(result)

    assert context.query == "Compare the invoices."
    assert context.is_empty is False
    assert context.document_ids == ["doc-1", "doc-2"]

    assert len(context.sources) == 2

    assert context.sources[0].document_id == "doc-1"
    assert context.sources[0].text == "Invoice total is 12000."

    assert context.sources[1].document_id == "doc-2"
    assert context.sources[1].text == "Invoice total is 15000."


def test_empty_retrieval_result_produces_empty_cross_document_context():
    result = RetrievalResult(
        query="Compare the invoices.",
        chunks=[],
    )

    adapter = CrossDocumentRetrievalAdapter()

    context = adapter.from_retrieval_result(result)

    assert context.is_empty is True
    assert context.document_ids == []