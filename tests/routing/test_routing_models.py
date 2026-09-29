from app.routing.models import QueryRequest, QueryRoute, QueryType


def test_query_type_values():
    assert QueryType.STRUCTURED.value == "structured"
    assert QueryType.SEMANTIC.value == "semantic"
    assert QueryType.CROSS_DOCUMENT.value == "cross_document"
    assert QueryType.UNKNOWN.value == "unknown"


def test_query_request():
    request = QueryRequest(
        query="What is the invoice total?"
    )

    assert request.query == "What is the invoice total?"


def test_query_route():
    route = QueryRoute(
        query="What is the invoice total?",
        query_type=QueryType.STRUCTURED,
    )

    assert route.query == "What is the invoice total?"
    assert route.query_type == QueryType.STRUCTURED