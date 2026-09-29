from dataclasses import dataclass, field

from app.analyst.models import Insight
from app.qa.llm import LLMClient
from app.qa.models import AnswerSource
from app.qa.verifier import EvidenceVerifier


@dataclass
class InsightGroundingContext:
    """Adapts an Insight's evidence into the shape app.qa's EvidenceVerifier expects."""

    query: str
    sources: list[AnswerSource] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.sources

    def as_text(self, separator: str = "\n\n---\n\n") -> str:
        return separator.join(source.text for source in self.sources)

    @classmethod
    def from_insight(cls, insight: Insight) -> "InsightGroundingContext":
        return cls(
            query=f"{insight.title}: {insight.description}",
            sources=[
                AnswerSource(
                    document_id=e.document_id,
                    document_type=e.document_type,
                    text=e.text,
                    page_number=e.page_number,
                )
                for e in insight.evidence
            ],
        )


class InsightPromptBuilder:
    SYSTEM_INSTRUCTIONS = """You are a document-analysis assistant explaining one finding to a business user.

Rules:
1. Use only the evidence given below -- do not invent facts, amounts, or dates not present in it.
2. Write 1-3 plain-English sentences a non-technical reviewer can act on.
3. State what was found and why it matters; do not restate the raw evidence verbatim.
"""

    def build(self, insight: Insight) -> str:
        evidence = "\n".join(f"- {e.text}" for e in insight.evidence) or "No evidence available."
        return (
            f"{self.SYSTEM_INSTRUCTIONS}\n"
            f"Finding type: {insight.type.value}\n"
            f"Severity: {insight.severity.value}\n"
            f"Title: {insight.title}\n"
            f"Description: {insight.description}\n\n"
            f"Evidence:\n{evidence}"
        )


class GroundedInsightGenerator:
    """
    Produces a plain-English narrative for an insight and verifies it
    against the insight's own evidence before attaching it -- an insight
    narrative is held to the same grounding bar as a QA answer.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        evidence_verifier: EvidenceVerifier,
        prompt_builder: InsightPromptBuilder | None = None,
    ):
        self._llm_client = llm_client
        self._verifier = evidence_verifier
        self._prompt_builder = prompt_builder or InsightPromptBuilder()

    def generate(self, insight: Insight) -> Insight:
        if not insight.evidence:
            return insight

        prompt = self._prompt_builder.build(insight)
        try:
            narrative = self._llm_client.generate(prompt)
        except Exception:
            # Best-effort: the insight (title/description/evidence) is
            # already complete without a narrative.
            return insight

        context = InsightGroundingContext.from_insight(insight)
        verification = self._verifier.verify(answer=narrative, context=context)

        if verification.verified:
            insight.narrative = narrative
            insight.narrative_verified = True
        else:
            insight.narrative_verified = False
            insight.metadata["narrative_rejected_reason"] = verification.reason

        return insight