import pytest

from app.indexing.config import QdrantSettings


def test_qdrant_settings_load_valid_environment(monkeypatch):
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setenv("QDRANT_COLLECTION", "document_chunks")
    monkeypatch.setenv("EMBEDDING_DIM", "384")
    monkeypatch.setenv("QDRANT_DISTANCE", "Cosine")

    settings = QdrantSettings.from_env()

    assert settings.url == "http://localhost:6333"
    assert settings.collection_name == "document_chunks"
    assert settings.vector_size == 384
    assert settings.distance == "Cosine"


def test_qdrant_settings_reject_invalid_embedding_dimension(monkeypatch):
    monkeypatch.setenv("EMBEDDING_DIM", "invalid")

    with pytest.raises(ValueError):
        QdrantSettings.from_env()


def test_qdrant_settings_reject_zero_embedding_dimension(monkeypatch):
    monkeypatch.setenv("EMBEDDING_DIM", "0")

    with pytest.raises(ValueError):
        QdrantSettings.from_env()


def test_qdrant_settings_reject_negative_embedding_dimension(monkeypatch):
    monkeypatch.setenv("EMBEDDING_DIM", "-1")

    with pytest.raises(ValueError):
        QdrantSettings.from_env()

def test_qdrant_settings_reject_empty_url(monkeypatch):
    monkeypatch.setenv("QDRANT_URL", "")

    with pytest.raises(ValueError, match="QDRANT_URL"):
        QdrantSettings.from_env()


def test_qdrant_settings_reject_empty_collection(monkeypatch):
    monkeypatch.setenv("QDRANT_COLLECTION", "")

    with pytest.raises(ValueError, match="QDRANT_COLLECTION"):
        QdrantSettings.from_env()

def test_qdrant_settings_reject_invalid_distance(monkeypatch):
    monkeypatch.setenv("QDRANT_DISTANCE", "InvalidDistance")

    with pytest.raises(ValueError, match="QDRANT_DISTANCE"):
        QdrantSettings.from_env()

def test_qdrant_settings_accept_valid_distance(monkeypatch):
    for distance in ("Cosine", "Euclid", "Dot"):
        monkeypatch.setenv("QDRANT_DISTANCE", distance)

        settings = QdrantSettings.from_env()

        assert settings.distance == distance
def test_qdrant_settings_loads_api_key(monkeypatch):
    monkeypatch.setenv("QDRANT_URL", "https://qdrant.example.com")
    monkeypatch.setenv("QDRANT_API_KEY", "super-secret-qdrant-key")
    monkeypatch.setenv("QDRANT_COLLECTION", "document_chunks")
    monkeypatch.setenv("EMBEDDING_DIM", "384")
    monkeypatch.setenv("QDRANT_DISTANCE", "Cosine")

    settings = QdrantSettings.from_env()

    assert settings.api_key == "super-secret-qdrant-key"

def test_qdrant_settings_reject_embedded_credentials(monkeypatch):
    monkeypatch.setenv(
        "QDRANT_URL",
        "https://admin:super-secret-password@qdrant.example.com:6333",
    )

    with pytest.raises(
        ValueError,
        match="embedded credentials",
    ):
        QdrantSettings.from_env()

def test_qdrant_settings_reject_invalid_collection_name(monkeypatch):
    for collection_name in (
        "../documents",
        "collection/name",
        "collection name",
        "collection$name",
    ):
        monkeypatch.setenv("QDRANT_COLLECTION", collection_name)

        with pytest.raises(
            ValueError,
            match="invalid characters",
        ):
            QdrantSettings.from_env()


def test_qdrant_settings_accepts_safe_collection_name(monkeypatch):
    monkeypatch.setenv(
        "QDRANT_COLLECTION",
        "document_chunks-v2",
    )

    settings = QdrantSettings.from_env()

    assert settings.collection_name == "document_chunks-v2"

def test_qdrant_settings_repr_does_not_expose_api_key():
    settings = QdrantSettings(
        url="https://qdrant.example.com",
        api_key="super-secret-qdrant-key",
        collection_name="document_chunks",
        vector_size=384,
        distance="Cosine",
        timeout=30,
    )

    representation = repr(settings)

    assert "super-secret-qdrant-key" not in representation
    assert "api_key" not in representation
def test_qdrant_settings_allows_local_http(monkeypatch):
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")

    settings = QdrantSettings.from_env()

    assert settings.url == "http://localhost:6333"


def test_qdrant_settings_rejects_remote_http(monkeypatch):
    monkeypatch.setenv("QDRANT_URL", "http://qdrant.example.com:6333")

    with pytest.raises(
        ValueError,
        match="HTTPS for non-local connections",
    ):
        QdrantSettings.from_env()

def test_qdrant_settings_rejects_noncanonical_distance_case(monkeypatch):
    for distance in ("cosine", "COSINE", "euclid", "EUCLID", "dot", "DOT"):
        monkeypatch.setenv("QDRANT_DISTANCE", distance)

        with pytest.raises(
            ValueError,
            match="QDRANT_DISTANCE",
        ):
            QdrantSettings.from_env()

def test_qdrant_settings_loads_timeout(monkeypatch):
    monkeypatch.setenv("QDRANT_TIMEOUT", "60")

    settings = QdrantSettings.from_env()

    assert settings.timeout == 60


def test_qdrant_settings_rejects_zero_timeout(monkeypatch):
    monkeypatch.setenv("QDRANT_TIMEOUT", "0")

    with pytest.raises(ValueError, match="QDRANT_TIMEOUT"):
        QdrantSettings.from_env()


def test_qdrant_settings_rejects_excessive_timeout(monkeypatch):
    monkeypatch.setenv("QDRANT_TIMEOUT", "301")

    with pytest.raises(ValueError, match="QDRANT_TIMEOUT"):
        QdrantSettings.from_env()

def test_qdrant_settings_allows_remote_https(monkeypatch):
    monkeypatch.setenv("QDRANT_URL", "https://qdrant.example.com:6333")

    settings = QdrantSettings.from_env()

    assert settings.url == "https://qdrant.example.com:6333"

def test_qdrant_settings_reject_url_without_hostname(monkeypatch):
    monkeypatch.setenv("QDRANT_URL", "https://")

    with pytest.raises(ValueError, match="hostname"):
        QdrantSettings.from_env()


def test_qdrant_settings_accepts_max_embedding_dimension(monkeypatch):
    monkeypatch.setenv("EMBEDDING_DIM", "16384")

    settings = QdrantSettings.from_env()

    assert settings.vector_size == 16384


def test_qdrant_settings_rejects_excessive_embedding_dimension(monkeypatch):
    monkeypatch.setenv("EMBEDDING_DIM", "16385")

    with pytest.raises(
        ValueError,
        match="must not exceed 16384",
    ):
        QdrantSettings.from_env()

def test_qdrant_settings_normalizes_api_key(monkeypatch):
    monkeypatch.setenv(
        "QDRANT_API_KEY",
        "  super-secret-qdrant-key  ",
    )

    settings = QdrantSettings.from_env()

    assert settings.api_key == "super-secret-qdrant-key"


def test_qdrant_settings_treats_whitespace_api_key_as_unset(monkeypatch):
    monkeypatch.setenv("QDRANT_API_KEY", "   ")

    settings = QdrantSettings.from_env()

    assert settings.api_key is None