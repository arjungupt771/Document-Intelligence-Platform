from dataclasses import dataclass, field

from app.qa.models import AnswerSource


@dataclass
class CrossDocumentContext:
    query: str
    sources: list[AnswerSource] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.sources

    @property
    def document_ids(self) -> list[str]:
        return list(dict.fromkeys(source.document_id for source in self.sources))

    def as_text(self) -> str:
        if self.is_empty:
            return "No evidence was retrieved for this question."

        sections = []

        for source in self.sources:
            sections.append(
                f"Document ID: {source.document_id}\n"
                f"Document Type: {source.document_type}\n"
                f"Evidence:\n"
                f"{source.text}"
            )

        return "\n\n---\n\n".join(sections)