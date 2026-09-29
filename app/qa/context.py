from dataclasses import dataclass, field
from typing import Protocol

from app.qa.models import AnswerSource


class GroundingContextLike(Protocol):
    query: str
    sources: list[AnswerSource]

    @property
    def is_empty(self) -> bool:
        ...



@dataclass
class GroundingContext:
    query: str
    sources: list[AnswerSource] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.sources

    def as_text(self, separator: str = "\n\n---\n\n") -> str:
        return separator.join(source.text for source in self.sources)

    @classmethod
    def from_retrieval_result(cls, result):
        return cls(
            query=result.query,
            sources=[
                AnswerSource(
                    document_id=chunk.document_id,
                    document_type=chunk.document_type,
                    text=chunk.text,
                    page_number=chunk.page_number,
                    score=chunk.score,
                )
                for chunk in result.chunks
            ],
        )