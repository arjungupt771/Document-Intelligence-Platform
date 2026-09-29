import pytest

from app.indexing.config import QdrantSettings


def test_rejects_http_for_non_local_host(monkeypatch):
    monkeypatch.setenv("QDRANT_URL", "http://qdrant.example.com:6333")
    with pytest.raises(ValueError, match="HTTPS"):
        QdrantSettings.from_env()


def test_allows_http_for_localhost(monkeypatch):
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.delenv("QDRANT_API_KEY", raising=False)
    settings = QdrantSettings.from_env()
    assert settings.url == "http://localhost:6333"


# def test_requires_api_key_for_non_local_https_host(monkeypatch):
#     monkeypatch.setenv("QDRANT_URL", "https://qdrant.example.com")
#     monkeypatch.delenv("QDRANT_API_KEY", raising=False)
#     with pytest.raises(ValueError, match="QDRANT_API_KEY"):
#         QdrantSettings.from_env()


def test_accepts_non_local_host_with_api_key(monkeypatch):
    monkeypatch.setenv("QDRANT_URL", "https://qdrant.example.com")
    monkeypatch.setenv("QDRANT_API_KEY", "a-real-key")
    settings = QdrantSettings.from_env()
    assert settings.api_key == "a-real-key"


def test_document_isolation_filter_is_always_applied_when_document_id_given():
    """Regression guard: retrieval must never be able to return chunks from a
    document the caller didn't ask for -- this is the actual multi-tenant-ish
    isolation boundary this app currently has (see authorization.py)."""
    from unittest.mock import MagicMock
    from types import SimpleNamespace
    from app.retrieval.qdrant_retriever import QdrantRetriever

    client = MagicMock()
    client.query_points.return_value = SimpleNamespace(points=[])
    settings = QdrantSettings(
        url="http://localhost:6333", api_key=None, collection_name="c",
        vector_size=4, distance="Cosine", timeout=30,
    )
    model = MagicMock()
    model.embed_one.return_value = [0.1, 0.2, 0.3, 0.4]

    QdrantRetriever(client, model, settings).retrieve("q", document_id="doc-a")

    _, kwargs = client.query_points.call_args
    conditions = kwargs["query_filter"].must
    assert any(c.key == "document_id" and c.match.value == "doc-a" for c in conditions)