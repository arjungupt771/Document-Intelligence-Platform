from __future__ import annotations

from typing import Optional

from qdrant_client import QdrantClient

from app.indexing.config import QdrantSettings


class ChunkEmbeddingSampler:
    """
    Samples chunk vectors already stored in Qdrant to build/compare
    embedding centroids -- no re-embedding needed.

    Known limitation: Qdrant `scroll` has no built-in recency ordering
    unless the payload carries a timestamp field. `DocumentIndexer`
    doesn't currently store one, so "current window" here means "a fresh
    sample of whatever's in the collection now", not strictly "the most
    recently indexed chunks". Add an `indexed_at` field to
    `DocumentIndexer._build_payload` and an index on it if you need true
    recency-windowed sampling later -- everything downstream of this
    class is unaffected by that change.
    """

    def __init__(self, client: QdrantClient, settings: QdrantSettings):
        self._client = client
        self._settings = settings

    def sample_centroid(self, limit: int = 500) -> Optional[list[float]]:
        records, _ = self._client.scroll(
            collection_name=self._settings.collection_name,
            limit=limit,
            with_vectors=True,
            with_payload=False,
        )
        vectors = [record.vector for record in records if record.vector]
        if not vectors:
            return None

        dim = len(vectors[0])
        return [sum(vector[i] for vector in vectors) / len(vectors) for i in range(dim)]