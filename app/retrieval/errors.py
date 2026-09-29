class RetrievalError(Exception):
    """Base exception for retrieval-layer failures."""


class QdrantConnectionError(RetrievalError):
    """Raised when Qdrant cannot be reached or queried."""


class QdrantWriteError(RetrievalError):
    """Raised when indexing (upsert/delete) against Qdrant fails."""