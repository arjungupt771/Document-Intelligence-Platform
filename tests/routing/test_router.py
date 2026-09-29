from app.routing.models import QueryRequest, QueryType
from app.routing.router import QueryRouter


def test_router_routes_structured_query():
    router = QueryRouter()

    request = QueryRequest(
        query="What is the total amount of invoice INV-1042?"
    )

    result = router.route(request)

    assert result.query == request.query
    assert result.query_type == QueryType.STRUCTURED


def test_router_routes_semantic_query():
    router = QueryRouter()

    request = QueryRequest(
        query="What does the contract say about termination?"
    )

    result = router.route(request)

    assert result.query == request.query
    assert result.query_type == QueryType.SEMANTIC


def test_router_routes_cross_document_query():
    router = QueryRouter()

    request = QueryRequest(
        query="Compare invoice INV-1042 and invoice INV-2048"
    )

    result = router.route(request)

    assert result.query == request.query
    assert result.query_type == QueryType.CROSS_DOCUMENT


def test_router_routes_unknown_query():
    router = QueryRouter()

    request = QueryRequest(
        query="Tell me something interesting"
    )

    result = router.route(request)

    assert result.query == request.query
    assert result.query_type == QueryType.UNKNOWN

def test_unknown_route_requires_clarification():
    router = QueryRouter()

    request = QueryRequest(
        query="Tell me something interesting"
    )

    result = router.route(request)

    assert router.requires_clarification(result) is True


def test_structured_route_does_not_require_clarification():
    router = QueryRouter()

    request = QueryRequest(
        query="What is the total amount?"
    )

    result = router.route(request)

    assert router.requires_clarification(result) is False


def test_semantic_route_does_not_require_clarification():
    router = QueryRouter()

    request = QueryRequest(
        query="What does the contract say about termination?"
    )

    result = router.route(request)

    assert router.requires_clarification(result) is False

def test_router_preserves_original_query():
    router = QueryRouter()

    request = QueryRequest(
        query="   What is the total amount?   "
    )

    result = router.route(request)

    assert result.query == request.query
    assert result.query_type == QueryType.STRUCTURED