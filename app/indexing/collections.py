from __future__ import annotations

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from app.indexing.config import QdrantSettings


def get_qdrant_client(settings: QdrantSettings) -> QdrantClient:
    return QdrantClient(
        url=settings.url,
        api_key=settings.api_key,
        timeout=settings.timeout,
        )


def ensure_collection(client: QdrantClient, settings: QdrantSettings) -> None:
    """
    Creates the collection if it doesn't exist yet, and makes sure the
    payload fields used for metadata filtering (document_id,
    document_type) are indexed. Without a payload index, filtering falls
    back to a full scan on every search -- fine for a demo, not for a
    real corpus. Safe to call repeatedly (e.g. on every app startup).

    NOTE: qdrant-client 1.10+ removed `.search()` in favor of
    `.query_points(query=...)` -- see app/retrieval/qdrant_retriever.py.
    """
    existing = {c.name for c in client.get_collections().collections}

    if settings.collection_name not in existing:
        client.create_collection(
            collection_name=settings.collection_name,
            vectors_config=qmodels.VectorParams(
                size=settings.vector_size,
                distance=qmodels.Distance[settings.distance.upper()],
            ),
        )

    for field_name in ("document_id", "document_type"):
        client.create_payload_index(
            collection_name=settings.collection_name,
            field_name=field_name,
            field_schema=qmodels.PayloadSchemaType.KEYWORD,
            )