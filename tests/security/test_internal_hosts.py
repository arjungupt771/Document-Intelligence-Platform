import pytest

from app.indexing.config import QdrantSettings
from app.storage.config import DatabaseSettings


def test_compose_service_names_rejected_by_default(monkeypatch):
    monkeypatch.delenv("INTERNAL_SERVICE_HOSTS", raising=False)
    monkeypatch.setenv("QDRANT_URL", "http://qdrant:6333")
    with pytest.raises(ValueError, match="HTTPS"):
        QdrantSettings.from_env()

    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://u:p@postgres:5432/db")
    monkeypatch.delenv("DATABASE_SSLMODE", raising=False)
    with pytest.raises(ValueError, match="DATABASE_SSLMODE"):
        DatabaseSettings.from_env()


def test_compose_service_names_allowed_when_explicitly_trusted(monkeypatch):
    monkeypatch.setenv("INTERNAL_SERVICE_HOSTS", "postgres,qdrant,redis")
    monkeypatch.setenv("QDRANT_URL", "http://qdrant:6333")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://u:p@postgres:5432/db")
    monkeypatch.delenv("DATABASE_SSLMODE", raising=False)

    assert QdrantSettings.from_env().url == "http://qdrant:6333"
    assert DatabaseSettings.from_env().url.endswith("@postgres:5432/db")


def test_untrusted_external_host_still_rejected(monkeypatch):
    monkeypatch.setenv("INTERNAL_SERVICE_HOSTS", "postgres,qdrant,redis")
    monkeypatch.setenv("QDRANT_URL", "http://qdrant.example.com:6333")
    with pytest.raises(ValueError, match="HTTPS"):
        QdrantSettings.from_env()