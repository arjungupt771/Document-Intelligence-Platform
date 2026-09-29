from __future__ import annotations

from functools import lru_cache

from app.indexing.config import EmbeddingSettings

_MINILM_L6_V2_DIM = 384


class EmbeddingModel:
    """
    Thin wrapper around sentence-transformers so the rest of the codebase
    (indexer, retriever) depends on this interface rather than the
    library directly -- swap models/providers here without touching
    them. The model is loaded lazily on first use, not at import time.
    """

    def __init__(self, settings: EmbeddingSettings = EmbeddingSettings()):
        self._settings = settings
        self._model = None

    @property
    def dimension(self) -> int:
        return _MINILM_L6_V2_DIM

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._settings.model_name)
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        model = self._load()
        vectors = model.encode(texts, normalize_embeddings=True)
        return [vector.tolist() for vector in vectors]

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]


@lru_cache(maxsize=1)
def get_embedding_model() -> EmbeddingModel:
    """Process-wide singleton so the (fairly large) model is loaded at most once."""
    return EmbeddingModel()
