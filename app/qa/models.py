from dataclasses import dataclass, field


@dataclass(frozen=True)
class AnswerRequest:
    query: str


@dataclass(frozen=True)
class AnswerSource:
    document_id: str
    document_type: str
    text: str
    page_number: int | None = None
    score: float | None = None


@dataclass
class AnswerResponse:
    query: str
    answer: str
    sources: list[AnswerSource] = field(default_factory=list)
    grounded: bool = False
    verified: bool = False
    unsupported_claims: list[str] = field(default_factory=list)
    verification_reason: str | None = None

