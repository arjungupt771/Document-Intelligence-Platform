from sqlalchemy.orm import Session

from app.analyst.generator import GroundedInsightGenerator, InsightPromptBuilder
from app.analyst.service import AnalystService
from app.qa.config import LLMSettings
from app.qa.deterministic_verifier import DeterministicEvidenceVerifier
from app.qa.groq_llm import GroqLLMClient
from app.storage.repository import DocumentRepository, ExtractionRepository, InsightRepository


def build_analyst_service(session: Session) -> AnalystService:
    """Build the production AnalystService and its runtime dependencies."""

    llm_client = GroqLLMClient(settings=LLMSettings.from_env())

    narrative_generator = GroundedInsightGenerator(
        llm_client=llm_client,
        evidence_verifier=DeterministicEvidenceVerifier(),
        prompt_builder=InsightPromptBuilder(),
    )

    return AnalystService(
        document_repository=DocumentRepository(session),
        extraction_repository=ExtractionRepository(session),
        insight_repository=InsightRepository(session),
        narrative_generator=narrative_generator,
    )