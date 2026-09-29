from __future__ import annotations

from sqlalchemy.orm import Session
from app.indexing.collections import get_qdrant_client
from app.indexing.config import QdrantSettings
from app.indexing.embeddings import get_embedding_model
from app.qa.config import LLMSettings
from app.qa.grounded_generator import GroundedAnswerGenerator
from app.qa.groq_llm import GroqLLMClient
from app.qa.service import QAService
from app.retrieval.qdrant_retriever import QdrantRetriever
from app.routing.router import QueryRouter
from app.routing.structured import StructuredQueryService
from app.storage.repository import DocumentRepository, ExtractionRepository
from app.qa.deterministic_verifier import DeterministicEvidenceVerifier

def build_qa_service(session: Session) -> QAService:
    """Build the production QA service and its runtime dependencies."""

    qdrant_settings = QdrantSettings.from_env()

    qdrant_client = get_qdrant_client(qdrant_settings)

    retriever = QdrantRetriever(
        client=qdrant_client,
        embedding_model=get_embedding_model(),
        settings=qdrant_settings,
    )

    structured_service = StructuredQueryService(
        document_repository=DocumentRepository(session),
        extraction_repository=ExtractionRepository(session),
    )

    llm_client = GroqLLMClient(
        settings=LLMSettings.from_env(),
    )

    answer_generator = GroundedAnswerGenerator(
        llm_client=llm_client,
    )

    return QAService(
        router=QueryRouter(),
        retriever=retriever,
        answer_generator=answer_generator,
        structured_service=structured_service,
        evidence_verifier=DeterministicEvidenceVerifier(),
    )