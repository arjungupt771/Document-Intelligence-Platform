from app.indexing.collections import get_qdrant_client
from app.indexing.config import QdrantSettings


def test_qdrant_client_receives_api_key(monkeypatch):
    captured = {}

    class FakeQdrantClient:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(
        "app.indexing.collections.QdrantClient",
        FakeQdrantClient,
    )

    settings = QdrantSettings(
        url="https://qdrant.example.com",
        api_key="super-secret-qdrant-key",
        collection_name="document_chunks",
        vector_size=384,
        distance="Cosine",
        timeout=30,
    )

    get_qdrant_client(settings)

    assert captured["url"] == "https://qdrant.example.com"
    assert captured["api_key"] == "super-secret-qdrant-key"


import pytest

from app.indexing.collections import ensure_collection, get_qdrant_client
from app.indexing.config import QdrantSettings


def test_ensure_collection_propagates_payload_index_errors():
    class FakeClient:
        def get_collections(self):
            return type(
                "CollectionsResponse",
                (),
                {"collections": []},
            )()

        def create_collection(self, **kwargs):
            pass

        def create_payload_index(self, **kwargs):
            raise RuntimeError("qdrant permission denied")

    settings = QdrantSettings(
        url="https://qdrant.example.com",
        api_key="secret",
        collection_name="document_chunks",
        vector_size=384,
        distance="Cosine",
        timeout=30,
    )

    with pytest.raises(RuntimeError, match="qdrant permission denied"):
        ensure_collection(FakeClient(), settings)