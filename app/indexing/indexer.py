from __future__ import annotations

import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from app.indexing.chunking import Chunk, chunk_document
from app.indexing.config import ChunkingSettings, QdrantSettings
from app.indexing.embeddings import EmbeddingModel
from app.parsing.models import ParsedDocument
from qdrant_client.http.exceptions import UnexpectedResponse
from app.retrieval.errors import QdrantWriteError
from app.retrieval.qdrant_faults import QDRANT_CONNECTIVITY_EXCEPTIONS, is_qdrant_server_fault

# Fixed namespace -> uuid5(namespace, name) is stable across processes/runs.
_POINT_NAMESPACE = uuid.UUID("5d0f8f0a-6f0a-4b8a-9a1a-2f6a7c9e0b11")


def _point_id(document_id: str, chunk_index: int) -> str:
    """Deterministic point ID: re-indexing the same chunk overwrites it (upsert), never duplicates it."""
    return str(uuid.uuid5(_POINT_NAMESPACE, f"{document_id}:{chunk_index}"))


class DocumentIndexer:
    def __init__(
        self,
        client: QdrantClient,
        embedding_model: EmbeddingModel,
        settings: QdrantSettings,
        chunking_settings: ChunkingSettings = ChunkingSettings(),
    ):
        self._client = client
        self._embedding_model = embedding_model
        self._settings = settings
        self._chunking_settings = chunking_settings

    def index_document(self, document, document_type, extra_metadata=None) -> int:
        chunks = chunk_document(document, self._chunking_settings)
        if not chunks:
            return 0

        vectors = self._embedding_model.embed([chunk.text for chunk in chunks])

        points = [
            qmodels.PointStruct(
                id=_point_id(document.document_id, chunk.chunk_index),
                vector=vector,
                payload=self._build_payload(document, document_type, chunk, extra_metadata),
            )
            for chunk, vector in zip(chunks, vectors)
        ]

        self._upsert_safely(points)
        return len(points)

    def reindex_document(
        self,
        document: ParsedDocument,
        document_type: str,
        extra_metadata: dict | None = None,
    ) -> int:
        """
        Full re-index. Plain index_document() alone would leave stale
        trailing chunks behind if the new version of the document is
        shorter than the old one (fewer chunk_index values) -- deleting
        first guarantees Qdrant only ever holds today's chunks.
        """
        self.delete_document(document.document_id)
        return self.index_document(document, document_type, extra_metadata)

    def delete_document(self, document_id: str) -> None:
        try:
            self._client.delete(
                collection_name=self._settings.collection_name,
                points_selector=qmodels.FilterSelector(
                    filter=qmodels.Filter(
                        must=[qmodels.FieldCondition(key="document_id", match=qmodels.MatchValue(value=document_id))]
                    )
                ),
            )
        except QDRANT_CONNECTIVITY_EXCEPTIONS as exc:
            raise QdrantWriteError("Failed to delete document vectors: vector store unavailable") from exc
        except UnexpectedResponse as exc:
            if is_qdrant_server_fault(exc):
                raise QdrantWriteError("Failed to delete document vectors: vector store unavailable") from exc
            raise

    def _upsert_safely(self, points) -> None:
        try:
            self._client.upsert(collection_name=self._settings.collection_name, points=points)
        except QDRANT_CONNECTIVITY_EXCEPTIONS as exc:
            raise QdrantWriteError("Failed to index document: vector store unavailable") from exc
        except UnexpectedResponse as exc:
            if is_qdrant_server_fault(exc):
                raise QdrantWriteError("Failed to index document: vector store unavailable") from exc
            raise

    @staticmethod
    def _build_payload(
        document: ParsedDocument,
        document_type: str,
        chunk: Chunk,
        extra_metadata: dict | None,
    ) -> dict:
        return {
            "document_id": document.document_id,
            "document_type": document_type,
            "source_filename": document.source_filename,
            "chunk_index": chunk.chunk_index,
            "page_number": chunk.page_number,
            "text": chunk.text,
        }
       
