from app.qa.context import GroundingContext
from app.qa.models import AnswerSource
from app.retrieval.models import RetrievedChunk, RetrievalResult

def test_empty_grounding_context():
    context = GroundingContext(
        query="What is the invoice total?"
    )

    assert context.query == "What is the invoice total?"
    assert context.sources == []
    assert context.is_empty is True


def test_grounding_context_with_sources():
    source_1 = AnswerSource(
        document_id="doc-1",
        document_type="invoice",
        text="Total amount: 12000",
    )

    source_2 = AnswerSource(
        document_id="doc-1",
        document_type="invoice",
        text="Vendor: ABC Ltd",
    )

    context = GroundingContext(
        query="What are the invoice details?",
        sources=[source_1, source_2],
    )

    assert context.is_empty is False
    assert len(context.sources) == 2


def test_grounding_context_as_text():
    source_1 = AnswerSource(
        document_id="doc-1",
        document_type="invoice",
        text="Total amount: 12000",
    )

    source_2 = AnswerSource(
        document_id="doc-1",
        document_type="invoice",
        text="Vendor: ABC Ltd",
    )

    context = GroundingContext(
        query="What are the invoice details?",
        sources=[source_1, source_2],
    )

    assert context.as_text() == (
        "Total amount: 12000"
        "\n\n---\n\n"
        "Vendor: ABC Ltd"
    )


def test_grounding_context_custom_separator():
    source_1 = AnswerSource(
        document_id="doc-1",
        document_type="invoice",
        text="Total amount: 12000",
    )

    source_2 = AnswerSource(
        document_id="doc-1",
        document_type="invoice",
        text="Vendor: ABC Ltd",
    )

    context = GroundingContext(
        query="What are the invoice details?",
        sources=[source_1, source_2],
    )

    assert context.as_text(separator="\n") == (
        "Total amount: 12000\nVendor: ABC Ltd"
    )

def test_from_retrieval_result_converts_chunks():
    result = RetrievalResult(
        query="What is the invoice total?",
        chunks=[
            RetrievedChunk(
                document_id="doc-1",
                document_type="invoice",
                chunk_index=0,
                page_number=1,
                text="Total amount: 12000",
                score=0.95,
            ),
            RetrievedChunk(
                document_id="doc-1",
                document_type="invoice",
                chunk_index=1,
                page_number=2,
                text="Vendor: ABC Ltd",
                score=0.88,
            ),
        ],
        total_candidates=2,
    )

    context = GroundingContext.from_retrieval_result(result)

    assert context.query == result.query
    assert len(context.sources) == 2

    assert context.sources[0] == AnswerSource(
        document_id="doc-1",
        document_type="invoice",
        text="Total amount: 12000",
        page_number=1,
        score=0.95,
    )

    assert context.sources[1] == AnswerSource(
        document_id="doc-1",
        document_type="invoice",
        text="Vendor: ABC Ltd",
        page_number=2,
        score=0.88,
    )

def test_from_empty_retrieval_result():
    result = RetrievalResult(
        query="What is the invoice total?",
        chunks=[],
        total_candidates=0,
    )

    context = GroundingContext.from_retrieval_result(result)

    assert context.query == result.query
    assert context.sources == []
    assert context.is_empty is True