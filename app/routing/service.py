from __future__ import annotations

from app.retrieval.interface import Retriever
from app.retrieval.models import RetrievalResult
from app.routing.models import QueryRequest, QueryRoute, QueryType, CrossDocumentRoute
from app.routing.router import QueryRouter
from app.routing.structured import StructuredQueryService


class QueryRoutingService:
    def __init__(
        self,
        router: QueryRouter,
        semantic_retriever: Retriever,
        structured_service: StructuredQueryService | None = None,
    ):
        self._router = router
        self._semantic_retriever = semantic_retriever
        self._structured_service = structured_service

    def route(self, request: QueryRequest) -> QueryRoute:
        return self._router.route(request)

    def retrieve_semantic(
        self,
        request: QueryRequest,
        top_k: int = 5,
        document_type: str | None = None,
        document_id: str | None = None,
        score_threshold: float | None = None,
    ) -> RetrievalResult:
        route = self.route(request)

        if route.query_type != QueryType.SEMANTIC:
            raise ValueError(
                f"Semantic retrieval requested for "
                f"{route.query_type.value} query"
            )

        return self._semantic_retriever.retrieve(
            query=request.query,
            top_k=top_k,
            document_type=document_type,
            document_id=document_id,
            score_threshold=score_threshold,
        )

    def get_structured_document(
        self,
        request: QueryRequest,
        document_id,
    ):
        route = self.route(request)

        if route.query_type != QueryType.STRUCTURED:
            raise ValueError(
                f"Structured retrieval requested for "
                f"{route.query_type.value} query"
            )

        if self._structured_service is None:
            raise RuntimeError(
                "StructuredQueryService is required for structured retrieval"
            )

        return self._structured_service.get_document(document_id)

    def get_structured_extraction(
        self,
        request: QueryRequest,
        document_id,
    ):
        route = self.route(request)

        if route.query_type != QueryType.STRUCTURED:
            raise ValueError(
                f"Structured retrieval requested for "
                f"{route.query_type.value} query"
            )

        if self._structured_service is None:
            raise RuntimeError(
                "StructuredQueryService is required for structured retrieval."
            )

        return self._structured_service.get_latest_extraction(
            document_id
        )

    def route_cross_document(
            self,
            request: QueryRequest,
    ) -> CrossDocumentRoute:
        route = self.route(request)

        if route.query_type != QueryType.CROSS_DOCUMENT:
            raise ValueError(
                f"Cross-document routing requested for"
                f"{route.query_type.value} query"
            )

        return CrossDocumentRoute(
            query = request.query
        )