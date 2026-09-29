import os
from dataclasses import dataclass,field
from typing import Optional
from urllib.parse import urlparse
import re
from app.security.internal_hosts import is_trusted_internal_host



MAX_EMBEDDING_DIM = 16_384

@dataclass(frozen=True)
class QdrantSettings:
    url: str
    api_key: Optional[str] = field(repr=False)
    collection_name: str
    vector_size: int
    distance: str
    timeout: int = 30

    @classmethod
    def from_env(cls) -> "QdrantSettings":
        url = os.getenv("QDRANT_URL", "http://localhost:6333")
        collection_name = os.getenv("QDRANT_COLLECTION", "document_chunks")
        vector_size = int(os.getenv("EMBEDDING_DIM", "384"))
        distance = os.getenv("QDRANT_DISTANCE", "Cosine")
        timeout = int(os.getenv("QDRANT_TIMEOUT", "30"))

        if timeout <=0:
            raise ValueError("QDRANT_TIMEOUT must be greater than 0")

        if timeout>300:
            raise ValueError("QDRANT_TIMEOUT must not exceed 300 seconds")

        if not url.strip():
            raise ValueError("QDRANT_URL must not be empty")

        parsed_url = urlparse(url)

        if parsed_url.scheme not in {"http", "https"}:
            raise ValueError("QDRANT_URL must use http or https")

        if not parsed_url.hostname:
            raise ValueError("QDRANT_URL must include a hostname")

        if parsed_url.username is not None or parsed_url.password is not None:
            raise ValueError(
                "QDRANT_URL must not contain embedded credentials"
                )

        local_hosts = {"localhost", "127.0.0.1", "::1"}

        if (
            parsed_url.scheme == "http"
            and parsed_url.hostname not in local_hosts
            and not is_trusted_internal_host(parsed_url.hostname)
        ):
            raise ValueError("QDRANT_URL must use HTTPS for non-local connections")

        api_key = (os.getenv("QDRANT_API_KEY") or "").strip() or None

        if not collection_name.strip():
            raise ValueError("QDRANT_COLLECTION must not be empty")

        if not re.fullmatch(r"[A-Za-z0-9_-]+", collection_name):
            raise ValueError(
                "QDRANT_COLLECTION contains invalid characters"
                )

        if vector_size <= 0:
            raise ValueError("EMBEDDING_DIM must be greater than 0")

        if vector_size > MAX_EMBEDDING_DIM:
            raise ValueError(
                f"EMBEDDING_DIM must not exceed {MAX_EMBEDDING_DIM}"
            )

        if distance not in {"Cosine", "Euclid", "Dot"}:
            raise ValueError("QDRANT_DISTANCE must be one of: Cosine, Euclid, Dot")

        return cls(
            url=url,
            api_key=(os.getenv("QDRANT_API_KEY") or "").strip() or None,
            collection_name=collection_name,
            vector_size=vector_size,
            distance=distance,
            timeout=timeout,
            )


@dataclass(frozen=True)
class ChunkingSettings:
    """Sizes are in words, not characters -- keeps chunks well within MiniLM's token window."""

    chunk_size: int = 220
    chunk_overlap: int = 40


@dataclass(frozen=True)
class EmbeddingSettings:
    model_name: str = "all-MiniLM-L6-v2"




