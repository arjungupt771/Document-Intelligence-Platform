from dataclasses import dataclass
from types import SimpleNamespace
import uuid
import pytest
from app.qa.verifier import EvidenceVerifier
from app.qa.verification import VerificationResult
from app.qa.verifier import EvidenceVerifier
from app.qa.verification import VerificationResult
from app.qa.models import AnswerRequest, AnswerResponse, AnswerSource
from app.qa.service import QAService
from app.retrieval.models import RetrievedChunk, RetrievalResult
from app.routing.models import QueryType, QueryRoute
from app.qa.generator import AnswerGenerator
from app.qa.models import AnswerRequest, AnswerResponse
class FakeStructuredService:
    def __init__(self, extraction=None):
        self.extraction = extraction
        self.calls = []

    def get_latest_extraction(self, document_id):
        self.calls.append(document_id)
        return self.extraction


class FakeRouter:
    def __init__(self, query_type=QueryType.SEMANTIC):
        self.query_type = query_type

    def route(self, request, has_document_id=False):
        return QueryRoute(
            query=request.query,
            query_type=self.query_type,
        )
class UnsupportedAnswerGenerator(AnswerGenerator):
    def generate(self, context):
        return AnswerResponse(
            query=context.query,
            answer="The invoice total is ₹50,000.",
            sources=context.sources,
            grounded=not context.is_empty,
        )

class FakeRetriever:
    def __init__(self, result=None):
        self.calls = []
        self.result = result

    def retrieve(
        self,
        query,
        top_k=5,
        document_type=None,
        document_id=None,
        score_threshold=None,
    ):
        self.calls.append(
            {
                "query": query,
                "top_k": top_k,
                "document_type": document_type,
                "document_id": document_id,
                "score_threshold": score_threshold,
            }
        )

        if self.result is not None:
            return self.result

        return RetrievalResult(
            query=query,
            chunks=[
                RetrievedChunk(
                    document_id="doc-1",
                    document_type="invoice",
                    chunk_index=0,
                    page_number=1,
                    text="The invoice total is ₹12,000.",
                    score=0.95,
                )
            ],
            total_candidates=1,
        )

class FakeAnswerGenerator:
    def __init__(self):
        self.context=None

    def generate(self, context):
        self.context = context

        return AnswerResponse(
            query=context.query,
            answer="The invoice total is ₹12,000.",
            sources=context.sources,
            grounded=not context.is_empty,
        )

class FakeEvidenceVerifier(EvidenceVerifier):
    def __init__(
        self,
        verified=True,
        unsupported_claims=None,
        reason=None,
    ):
        self.result = VerificationResult(
            verified=verified,
            unsupported_claims=unsupported_claims or [],
            reason=reason,
        )
        self.calls = 0

    def verify(self, answer, context):
        self.calls += 1
        return self.result

def test_structured_query_uses_extraction_as_grounding():
    document_id = uuid.uuid4()

    extraction = SimpleNamespace(
        document_id=document_id,
        document_type=SimpleNamespace(value="invoice"),
        data={
            "invoice_number": "INV-1001",
            "total_amount": 12000,
        },
    )

    router = FakeRouter(QueryType.STRUCTURED)
    retriever = FakeRetriever()
    structured_service = FakeStructuredService(extraction)
    generator = FakeAnswerGenerator()

    service = QAService(
        router=router,
        retriever=retriever,
        answer_generator=generator,
        structured_service=structured_service,
    )

    result = service.answer(
        AnswerRequest(query="What is the invoice total?"),
        document_id=document_id,
    )

    assert result.grounded is True
    assert len(result.sources) == 1

    assert structured_service.calls == [document_id]
    assert retriever.calls == []

    assert result.sources[0].text == (
        "Field: total_amount\n"
        "Value: 12000"
    )

def test_semantic_answer_can_fail_verification():
    verifier = FakeEvidenceVerifier(
        verified=False,
        unsupported_claims=["The payment deadline is 30 days."],
        reason="Unsupported claim.",
    )

    service = QAService(
        router=FakeRouter(),
        retriever=FakeRetriever(),
        answer_generator=FakeAnswerGenerator(),
        evidence_verifier=verifier,
    )

    response = service.answer(
        AnswerRequest(query="What are the payment terms?")
    )

    assert response.verified is False
    assert response.unsupported_claims == [
        "The payment deadline is 30 days."
    ]
    assert response.verification_reason == "Unsupported claim."


def test_semantic_answer_is_verified_when_verifier_is_configured():
    verifier = FakeEvidenceVerifier(
        verified=True,
        reason="Answer is supported.",
    )

    service = QAService(
        router=FakeRouter(),
        retriever=FakeRetriever(),
        answer_generator=FakeAnswerGenerator(),
        evidence_verifier=verifier,
    )

    response = service.answer(
        AnswerRequest(query="What are the payment terms?")
    )

    assert response.verified is True
    assert response.verification_reason == "Answer is supported."


def test_semantic_query_is_retrieved_and_answered():
    router = FakeRouter(QueryType.SEMANTIC)
    retriever = FakeRetriever()
    generator = FakeAnswerGenerator()

    service = QAService(
        router=router,
        retriever=retriever,
        answer_generator=generator,
    )

    result = service.answer(
        AnswerRequest(query="What is the invoice total?")
    )

    assert result.answer == "The invoice total is ₹12,000."
    assert result.grounded is True

    assert len(retriever.calls) == 1
    assert retriever.calls[0]["query"] == "What is the invoice total?"

    assert generator.context is not None
    assert generator.context.query == "What is the invoice total?"
    assert len(generator.context.sources) == 1
    assert generator.context.sources[0].text == (
        "The invoice total is ₹12,000."
    )


def test_retrieval_options_are_forwarded():
    router = FakeRouter(QueryType.SEMANTIC)
    retriever = FakeRetriever()
    generator = FakeAnswerGenerator()

    service = QAService(
        router=router,
        retriever=retriever,
        answer_generator=generator,
    )

    service.answer(
        AnswerRequest(query="Explain the payment terms."),
        top_k=10,
        document_type="contract",
        document_id="doc-42",
        score_threshold=0.75,
    )

    assert retriever.calls[0] == {
        "query": "Explain the payment terms.",
        "top_k": 10,
        "document_type": "contract",
        "document_id": "doc-42",
        "score_threshold": 0.75,
    }


def test_unknown_query_is_rejected_before_retrieval():
    router = FakeRouter(QueryType.UNKNOWN)
    retriever = FakeRetriever()
    generator = FakeAnswerGenerator()

    service = QAService(
        router=router,
        retriever=retriever,
        answer_generator=generator,
    )

    with pytest.raises(
        ValueError,
        match="could not be classified",
    ):
        service.answer(
            AnswerRequest(query="Something unclear")
        )

    assert retriever.calls == []


def test_structured_query_requires_structured_service():
    router = FakeRouter(QueryType.STRUCTURED)
    retriever = FakeRetriever()
    generator = FakeAnswerGenerator()

    service = QAService(
        router=router,
        retriever=retriever,
        answer_generator=generator,
    )

    with pytest.raises(
        ValueError,
        match="Structured query support is not configured",
    ):
        service.answer(
            AnswerRequest(query="What is the invoice total?"),
            document_id="doc-1",
        )

    assert retriever.calls == []

def test_structured_query_requires_extraction():
    document_id = uuid.uuid4()

    router = FakeRouter(QueryType.STRUCTURED)
    retriever = FakeRetriever()
    structured_service = FakeStructuredService(extraction=None)
    generator = FakeAnswerGenerator()

    service = QAService(
        router=router,
        retriever=retriever,
        answer_generator=generator,
        structured_service=structured_service,
    )

    with pytest.raises(
        ValueError,
        match="No extraction found",
    ):
        service.answer(
            AnswerRequest(query="What is the invoice total?"),
            document_id=document_id,
        )

    assert structured_service.calls == [document_id]

def test_structured_query_requires_document_id():
    router = FakeRouter(QueryType.STRUCTURED)
    retriever = FakeRetriever()
    structured_service = FakeStructuredService()
    generator = FakeAnswerGenerator()

    service = QAService(
        router=router,
        retriever=retriever,
        answer_generator=generator,
        structured_service=structured_service,
    )

    with pytest.raises(
        ValueError,
        match="document_id is required",
    ):
        service.answer(
            AnswerRequest(query="What is the invoice total?")
        )

    assert structured_service.calls == []

def test_structured_query_requires_structured_service():
    router = FakeRouter(QueryType.STRUCTURED)
    retriever = FakeRetriever()
    generator = FakeAnswerGenerator()

    service = QAService(
        router=router,
        retriever=retriever,
        answer_generator=generator,
    )

    with pytest.raises(
        ValueError,
        match="Structured query support is not configured",
    ):
        service.answer(
            AnswerRequest(query="What is the invoice total?"),
            document_id="doc-1",
        )

def test_default_verifier_runs_when_no_verifier_is_supplied():
    service = QAService(
        router=FakeRouter(QueryType.SEMANTIC),
        retriever=FakeRetriever(),
        answer_generator=FakeAnswerGenerator(),
    )

    response = service.answer(
        AnswerRequest(query="What is the invoice total?")
    )

    assert response.verified is True
    assert response.unsupported_claims == []
    assert response.verification_reason is not None

def test_default_verifier_rejects_unsupported_answer():
    service = QAService(
        router=FakeRouter(QueryType.SEMANTIC),
        retriever=FakeRetriever(),
        answer_generator=UnsupportedAnswerGenerator(),
    )

    response = service.answer(
        AnswerRequest(query="What is the invoice total?")
    )

    assert response.grounded is True
    assert response.verified is False
    assert response.unsupported_claims == [
        "The invoice total is ₹50,000"
    ]
    assert response.verification_reason is not None

def test_qa_service_verifies_semantic_answer():
    router = FakeRouter(QueryType.SEMANTIC)

    retriever = FakeRetriever()
    generator = FakeAnswerGenerator()

    verifier = FakeEvidenceVerifier(
        
            verified=True,
            unsupported_claims=[],
            reason="Evidence supports the answer.",
        
    )

    service = QAService(
        router=router,
        retriever=retriever,
        answer_generator=generator,
        evidence_verifier=verifier,
    )

    response = service.answer(
        AnswerRequest(query="What is the invoice total?")
    )

    assert response.verified is True
    assert response.unsupported_claims == []
    assert response.verification_reason == "Evidence supports the answer."
    assert generator.context is not None
    assert verifier.calls == 1

def test_qa_service_does_not_verify_unknown_query():
    router = FakeRouter(QueryType.UNKNOWN)

    retriever = FakeRetriever()
    generator = FakeAnswerGenerator()

    verifier = FakeEvidenceVerifier(
        VerificationResult(
            verified=True,
            unsupported_claims=[],
            reason="Should not be called.",
        )
    )

    service = QAService(
        router=router,
        retriever=retriever,
        answer_generator=generator,
        evidence_verifier=verifier,
    )

    with pytest.raises(ValueError):
        service.answer(
            AnswerRequest(query="Unknown question")
        )

    assert verifier.calls == 0


def test_qa_service_handles_empty_semantic_evidence():
    router = FakeRouter(QueryType.SEMANTIC)

    retriever = FakeRetriever()
    retriever.result = RetrievalResult(
        query="What is the invoice total?",
        chunks=[],
    )

    generator = FakeAnswerGenerator()

    verifier = FakeEvidenceVerifier(
        verified=False,
        unsupported_claims=[],
        reason="No evidence is available for verification.",
    )

    service = QAService(
        router=router,
        retriever=retriever,
        answer_generator=generator,
        evidence_verifier=verifier,
    )

    response = service.answer(
        AnswerRequest(query="What is the invoice total?")
    )

    assert response.sources == []
    assert response.grounded is False
    assert response.verified is False
    assert response.verification_reason == (
        "No evidence is available for verification."
    )
    assert verifier.calls == 1

def test_qa_service_propagates_retrieval_failure():
    router = FakeRouter(QueryType.SEMANTIC)

    class FailingRetriever:
        def retrieve(
            self,
            query,
            top_k=5,
            document_type=None,
            document_id=None,
            score_threshold=None,
        ):
            raise RuntimeError("Retrieval backend unavailable.")

    generator = FakeAnswerGenerator()

    verifier = FakeEvidenceVerifier(
        verified=True,
        reason="Should not be called.",
    )

    service = QAService(
        router=router,
        retriever=FailingRetriever(),
        answer_generator=generator,
        evidence_verifier=verifier,
    )

    with pytest.raises(RuntimeError, match="Retrieval backend unavailable."):
        service.answer(
            AnswerRequest(query="What is the invoice total?")
        )

    assert verifier.calls == 0

def test_qa_service_propagates_answer_generation_failure():
    router = FakeRouter(QueryType.SEMANTIC)

    retriever = FakeRetriever()

    class FailingAnswerGenerator(AnswerGenerator):
        def generate(self, context):
            raise RuntimeError("Answer generation failed.")

    verifier = FakeEvidenceVerifier(
        verified=True,
        reason="Should not be called.",
    )

    service = QAService(
        router=router,
        retriever=retriever,
        answer_generator=FailingAnswerGenerator(),
        evidence_verifier=verifier,
    )

    with pytest.raises(
        RuntimeError,
        match="Answer generation failed.",
    ):
        service.answer(
            AnswerRequest(query="What is the invoice total?")
        )

    assert verifier.calls == 0

def test_qa_service_propagates_verification_failure():
    router = FakeRouter(QueryType.SEMANTIC)

    retriever = FakeRetriever()
    generator = FakeAnswerGenerator()

    class FailingEvidenceVerifier(EvidenceVerifier):
        def verify(self, answer, context):
            raise RuntimeError("Verification failed.")

    service = QAService(
        router=router,
        retriever=retriever,
        answer_generator=generator,
        evidence_verifier=FailingEvidenceVerifier(),
    )

    with pytest.raises(
        RuntimeError,
        match="Verification failed.",
    ):
        service.answer(
            AnswerRequest(query="What is the invoice total?")
        )