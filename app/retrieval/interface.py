from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.retrieval.models import RetrievalResult


class Retriever(ABC):
    """
    Retrieval interface the rest of the app depends on -- callers (chat,
    Q&A endpoints) never talk to Qdrant directly.

    Not every read path should go through this: a use case that needs
    *all* matching records rather than the top-k most similar ones
    (e.g. a coverage/compliance-style report) should query the
    repository/collection directly instead of squeezing itself through
    a similarity-search interface.
    """

    @abstractmethod
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        document_type: Optional[str] = None,
        document_id: Optional[str] = None,
        score_threshold: Optional[float] = None,
    ) -> RetrievalResult:
        raise NotImplementedError
