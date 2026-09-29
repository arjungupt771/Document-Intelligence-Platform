import time
from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from app.retrieval.errors import QdrantConnectionError
from app.indexing.config import QdrantSettings
from app.indexing.embeddings import EmbeddingModel
from app.observability.metrics import RETRIEVAL_LATENCY, RETRIEVAL_RESULT_TOTAL
from app.retrieval.interface import Retriever
from app.retrieval.models import RetrievalResult, RetrievedChunk
from qdrant_client.http.exceptions import UnexpectedResponse
from app.retrieval.qdrant_faults import QDRANT_CONNECTIVITY_EXCEPTIONS, is_qdrant_server_fault

DEFAULT_SCORE_THRESHOLD = 0.2


class QdrantRetriever(Retriever):
    def __init__(
        self,
        client: QdrantClient,
        embedding_model: EmbeddingModel,
        settings: QdrantSettings,
        default_score_threshold: float = DEFAULT_SCORE_THRESHOLD,
    ):
        self._client = client
        self._embedding_model = embedding_model
        self._settings = settings
        self._default_score_threshold = default_score_threshold

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        document_type: Optional[str] = None,
        document_id: Optional[str] = None,
        score_threshold: Optional[float] = None,
    ) -> RetrievalResult:
        start = time.perf_counter()
        try:
            result = self._retrieve(query, top_k, document_type, document_id, score_threshold)
        finally:
            RETRIEVAL_LATENCY.observe(time.perf_counter() - start)

        RETRIEVAL_RESULT_TOTAL.labels(result="empty" if result.is_empty else "hit").inc()
        return result

    def _retrieve(
        self,
        query: str,
        top_k: int,
        document_type: Optional[str],
        document_id: Optional[str],
        score_threshold: Optional[float],
    ) -> RetrievalResult:
        if not query or not query.strip():
            return RetrievalResult(query=query, chunks=[], total_candidates=0)

        query_vector = self._embedding_model.embed_one(query)
        query_filter = self._build_filter(document_type, document_id)
        threshold = self._default_score_threshold if score_threshold is None else score_threshold
        try:
           response = self._client.query_points(
               collection_name=self._settings.collection_name,
               query=query_vector,
               query_filter=query_filter,
               limit=top_k,
               score_threshold=threshold,
               with_payload=True,
             )
        except QDRANT_CONNECTIVITY_EXCEPTIONS as exc:
            raise QdrantConnectionError(
                "Vector search service is unavailable"
            ) from exc
        except UnexpectedResponse as exc:
            if is_qdrant_server_fault(exc):
                raise QdrantConnectionError("Vector search service is unavailable") from exc
            raise
         

        points = response.points
        chunks = [self._to_chunk(point) for point in points]
        chunks.sort(key=lambda c: c.score, reverse=True)

        return RetrievalResult(query=query, chunks=chunks, total_candidates=len(points))

    @staticmethod
    def _build_filter(document_type: Optional[str], document_id: Optional[str]) -> Optional[qmodels.Filter]:
        conditions = []
        if document_type is not None:
            conditions.append(
                qmodels.FieldCondition(key="document_type", match=qmodels.MatchValue(value=document_type))
            )
        if document_id is not None:
            conditions.append(
                qmodels.FieldCondition(key="document_id", match=qmodels.MatchValue(value=document_id))
            )
        return qmodels.Filter(must=conditions) if conditions else None

    @staticmethod
    def _to_chunk(point) -> RetrievedChunk:
        payload = point.payload or {}
        return RetrievedChunk(
            document_id=payload.get("document_id", ""),
            document_type=payload.get("document_type", ""),
            chunk_index=payload.get("chunk_index", -1),
            page_number=payload.get("page_number"),
            text=payload.get("text", ""),
            score=point.score,
        )
