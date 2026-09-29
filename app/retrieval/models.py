from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RetrievedChunk:
    document_id: str
    document_type: str
    chunk_index: int
    page_number: int | None
    text: str
    score: float


@dataclass
class RetrievalResult:
    query: str
    chunks: list[RetrievedChunk] = field(default_factory=list)
    total_candidates: int = 0
    """How many points matched (filter + threshold) before top_k truncation -- retrieval metadata for logging/debugging."""

    @property
    def is_empty(self) -> bool:
        return len(self.chunks) == 0

    def assembled_context(self, separator: str = "\n\n---\n\n") -> str:
        """
        Concatenates retrieved chunks into a single context block for a
        prompt, most relevant first, each one traceable back to its
        source document and page.
        """
        if self.is_empty:
            return ""

        parts = []
        for chunk in self.chunks:
            header = f"[{chunk.document_type} | doc={chunk.document_id} | page={chunk.page_number}]"
            parts.append(f"{header}\n{chunk.text}")
        return separator.join(parts)
