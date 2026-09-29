from app.qa.models import AnswerRequest, AnswerResponse, AnswerSource


def test_answer_request_stores_query():
    request = AnswerRequest(query="What is the invoice total?")

    assert request.query == "What is the invoice total?"


def test_answer_source_stores_document_metadata():
    source = AnswerSource(
        document_id="doc-123",
        document_type="invoice",
        text="Total amount: 12000",
        page_number=2,
        score=0.91,
    )

    assert source.document_id == "doc-123"
    assert source.document_type == "invoice"
    assert source.text == "Total amount: 12000"
    assert source.page_number == 2
    assert source.score == 0.91


def test_answer_response_defaults():
    response = AnswerResponse(
        query="What is the invoice total?",
        answer="The total is 12000.",
    )

    assert response.sources == []
    assert response.grounded is False


def test_answer_response_stores_sources():
    source_1 = AnswerSource(
        document_id="doc-1",
        document_type="invoice",
        text="Total: 12000",
    )

    source_2 = AnswerSource(
        document_id="doc-2",
        document_type="invoice",
        text="Vendor: ABC Ltd",
    )

    response = AnswerResponse(
        query="What are the invoice details?",
        answer="The invoice total is 12000 and the vendor is ABC Ltd.",
        sources=[source_1, source_2],
        grounded=True,
    )

    assert len(response.sources) == 2
    assert response.sources[0] == source_1
    assert response.sources[1] == source_2
    assert response.grounded is True