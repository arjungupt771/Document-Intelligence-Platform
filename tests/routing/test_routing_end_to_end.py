from app.routing.models import QueryRequest, QueryType
from app.routing.router import QueryRouter


def test_structured_query_end_to_end():
    router = QueryRouter()

    request = QueryRequest(
        query="What is the total amount of invoice INV-1042?"
    )

    result = router.route(request)

    assert result.query == request.query
    assert result.query_type == QueryType.STRUCTURED


def test_semantic_query_end_to_end():
    router = QueryRouter()

    request = QueryRequest(
        query="What does the contract say about termination?"
    )

    result = router.route(request)

    assert result.query == request.query
    assert result.query_type == QueryType.SEMANTIC


def test_cross_document_query_end_to_end():
    router = QueryRouter()

    request = QueryRequest(
        query="Compare the total amount between invoices INV-1042 and INV-2048"
    )

    result = router.route(request)

    assert result.query == request.query
    assert result.query_type == QueryType.CROSS_DOCUMENT


def test_unknown_query_end_to_end():
    router = QueryRouter()

    request = QueryRequest(
        query="Tell me something interesting"
    )

    result = router.route(request)

    assert result.query == request.query
    assert result.query_type == QueryType.UNKNOWN