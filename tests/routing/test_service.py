from unittest.mock import MagicMock

import pytest

from app.retrieval.models import RetrievalResult
from app.routing.models import QueryRequest, QueryRoute, QueryType
from app.routing.router import QueryRouter
from app.routing.service import QueryRoutingService
import uuid
from unittest.mock import MagicMock
from app.routing.models import CrossDocumentRoute
from app.retrieval.models import RetrievalResult
from app.routing.models import QueryRequest, QueryRoute, QueryType
from app.routing.router import QueryRouter
from app.routing.service import QueryRoutingService
from app.routing.structured import StructuredQueryService


def test_cross_document_route_is_created():
    router = MagicMock(spec=QueryRouter)
    retriever = MagicMock()
    structured = MagicMock(spec=StructuredQueryService)

    router.route.return_value = QueryRoute(
        query="Compare invoice INV-1042 and invoice INV-2048",
        query_type=QueryType.CROSS_DOCUMENT,
    )

    service = QueryRoutingService(
        router,
        retriever,
        structured,
    )

    request = QueryRequest(
        query="Compare invoice INV-1042 and invoice INV-2048"
    )

    result = service.route_cross_document(request)

    assert isinstance(result, CrossDocumentRoute)
    assert result.query == request.query
    assert result.query_type == QueryType.CROSS_DOCUMENT

    retriever.retrieve.assert_not_called()
    structured.get_document.assert_not_called()
    structured.get_latest_extraction.assert_not_called()


def test_non_cross_document_query_is_rejected():
    router = MagicMock(spec=QueryRouter)
    retriever = MagicMock()
    structured = MagicMock(spec=StructuredQueryService)

    router.route.return_value = QueryRoute(
        query="What is the total amount?",
        query_type=QueryType.STRUCTURED,
    )

    service = QueryRoutingService(
        router,
        retriever,
        structured,
    )

    request = QueryRequest(
        query="What is the total amount?"
    )

    with pytest.raises(
        ValueError,
        match="Cross-document routing requested",
    ):
        service.route_cross_document(request)

def test_semantic_query_is_delegated_to_retriever():
    router = MagicMock(spec=QueryRouter)
    retriever = MagicMock()

    router.route.return_value = QueryRoute(
        query="What does the contract say about termination?",
        query_type=QueryType.SEMANTIC,
    )

    expected = RetrievalResult(
        query="What does the contract say about termination?"
    )
    retriever.retrieve.return_value = expected

    service = QueryRoutingService(router, retriever)

    request = QueryRequest(
        query="What does the contract say about termination?"
    )

    result = service.retrieve_semantic(
        request,
        top_k=3,
        document_type="contract",
        document_id="doc-1",
        score_threshold=0.4,
    )

    assert result is expected

    retriever.retrieve.assert_called_once_with(
        query=request.query,
        top_k=3,
        document_type="contract",
        document_id="doc-1",
        score_threshold=0.4,
    )


def test_non_semantic_query_is_rejected():
    router = MagicMock(spec=QueryRouter)
    retriever = MagicMock()

    router.route.return_value = QueryRoute(
        query="What is the total amount?",
        query_type=QueryType.STRUCTURED,
    )

    service = QueryRoutingService(router, retriever)

    request = QueryRequest(
        query="What is the total amount?"
    )

    with pytest.raises(ValueError, match="Semantic retrieval requested"):
        service.retrieve_semantic(request)

    retriever.retrieve.assert_not_called()


def test_structured_document_lookup_is_delegated():
    router = MagicMock(spec=QueryRouter)
    retriever = MagicMock()
    structured = MagicMock(spec=StructuredQueryService)

    router.route.return_value = QueryRoute(
        query="What is the invoice?",
        query_type=QueryType.STRUCTURED,
    )

    document_id = uuid.uuid4()
    expected = MagicMock()

    structured.get_document.return_value = expected

    service = QueryRoutingService(
        router,
        retriever,
        structured,
    )

    request = QueryRequest(
        query="What is the invoice?"
    )

    result = service.get_structured_document(
        request,
        document_id,
    )

    assert result is expected
    structured.get_document.assert_called_once_with(
        document_id
    )

    retriever.retrieve.assert_not_called()


def test_structured_extraction_lookup_is_delegated():
    router = MagicMock(spec=QueryRouter)
    retriever = MagicMock()
    structured = MagicMock(spec=StructuredQueryService)

    router.route.return_value = QueryRoute(
        query="What is the total amount?",
        query_type=QueryType.STRUCTURED,
    )

    document_id = uuid.uuid4()
    expected = MagicMock()

    structured.get_latest_extraction.return_value = expected

    service = QueryRoutingService(
        router,
        retriever,
        structured,
    )

    request = QueryRequest(
        query="What is the total amount?"
    )

    result = service.get_structured_extraction(
        request,
        document_id,
    )

    assert result is expected

    structured.get_latest_extraction.assert_called_once_with(
        document_id
    )


def test_semantic_path_does_not_call_structured_service():
    router = MagicMock(spec=QueryRouter)
    retriever = MagicMock()
    structured = MagicMock(spec=StructuredQueryService)

    router.route.return_value = QueryRoute(
        query="What does the contract say about termination?",
        query_type=QueryType.SEMANTIC,
    )

    expected = RetrievalResult(
        query="What does the contract say about termination?"
    )

    retriever.retrieve.return_value = expected

    service = QueryRoutingService(
        router,
        retriever,
        structured,
    )

    request = QueryRequest(
        query="What does the contract say about termination?"
    )

    result = service.retrieve_semantic(request)

    assert result is expected
    structured.get_document.assert_not_called()
    structured.get_latest_extraction.assert_not_called()