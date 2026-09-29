from app.qa.context import GroundingContext, GroundingContextLike
from app.qa.deterministic_verifier import DeterministicEvidenceVerifier
from app.qa.models import AnswerRequest, AnswerResponse, AnswerSource
from app.qa.verifier import EvidenceVerifier
from app.routing.models import QueryRequest, QueryType

from app.qa.generator import AnswerGenerator
from app.qa.llm import LLMClient
from app.qa.prompt import GroundedPromptBuilder


class QAService:
    def __init__(
        self,
        router,
        retriever,
        answer_generator,
        structured_service=None,
        evidence_verifier: EvidenceVerifier | None = None,
    ):
        self._router = router
        self._retriever = retriever
        self._answer_generator = answer_generator
        self._structured_service = structured_service
        self._evidence_verifier = (
            evidence_verifier or DeterministicEvidenceVerifier()
        )

    def _structured_context(self, query: str, document_id: str | None):
        """Grounding from the saved extraction, or None if it can't be built."""
        if self._structured_service is None:
            raise ValueError("Structured query support is not configured")

        if document_id is None:
            return None

        extraction = self._structured_service.get_latest_extraction(document_id)
        data = (extraction.data or {}) if extraction is not None else {}
        if not data:
            return None

        query_tokens = set(query.casefold().replace("?", " ").split())
        query_tokens -= {"what", "is", "the", "a", "an", "of", "for", "invoice", "document"}

        scored = []
        for field, value in data.items():
            field_tokens = set(str(field).casefold().replace("_", " ").split())
            score = len(field_tokens & query_tokens)
            if score:
                scored.append((score, field, value))

        if scored:
            best = max(s for s, _, _ in scored)
            matching = [(f, v) for s, f, v in scored if s == best]
        else:
            matching = list(data.items())

        document_type_value = (
            extraction.document_type.value
            if hasattr(extraction.document_type, "value")
            else str(extraction.document_type)
        )

        return GroundingContext(
            query=query,
            sources=[
                AnswerSource(
                    document_id=str(extraction.document_id),
                    document_type=document_type_value,
                    text=f"Field: {field}\nValue: {value}",
                )
                for field, value in matching
            ],
        )

    def answer(
        self,
        request: AnswerRequest,
        top_k: int = 5,
        document_type: str | None = None,
        document_id: str | None = None,
        score_threshold: float | None = None,
    ) -> AnswerResponse:
        route = self._router.route(
            QueryRequest(query=request.query),
            has_document_id=document_id is not None,
        )
        query_type = route.query_type

        if query_type == QueryType.UNKNOWN:
            raise ValueError(
                "The query could not be classified. "
                "Please ask a more specific question."
            )

        context = None

        if query_type == QueryType.STRUCTURED:
            context = self._structured_context(request.query, document_id)
            if context is None:
                # No document scope or no saved extraction: search the
                # indexed text instead of failing the request.
                query_type = QueryType.SEMANTIC

        if query_type == QueryType.SEMANTIC:
            retrieval = self._retriever.retrieve(
                query=request.query,
                top_k=top_k,
                document_type=document_type,
                document_id=document_id,
                score_threshold=score_threshold,
            )
            context = GroundingContext.from_retrieval_result(retrieval)
        elif context is None:
            raise ValueError(f"Unsupported query type: {query_type.value}")

        result = self._answer_generator.generate(context)

        if query_type == QueryType.SEMANTIC:
            verification = self._evidence_verifier.verify(result.answer, context)
            result.verified = verification.verified
            result.unsupported_claims = verification.unsupported_claims
            result.verification_reason = verification.reason

        return result

INSUFFICIENT_EVIDENCE_ANSWER = (
    "I don't have sufficient evidence in the provided document to answer that question."
)


class GroundedAnswerGenerator(AnswerGenerator):
    def __init__(
        self,
        llm_client: LLMClient,
        prompt_builder: GroundedPromptBuilder | None = None,
    ):
        self._llm_client = llm_client
        self._prompt_builder = prompt_builder or GroundedPromptBuilder()

    def generate(self, context: GroundingContextLike) -> AnswerResponse:
        if context.is_empty:
            # Never ask the model to answer without evidence -- it would invent a value.
            return AnswerResponse(
                query=context.query,
                answer=INSUFFICIENT_EVIDENCE_ANSWER,
                sources=[],
                grounded=False,
            )

        prompt = self._prompt_builder.build(context)
        answer = self._llm_client.generate(prompt)

        return AnswerResponse(
            query=context.query,
            answer=answer,
            sources=context.sources,
            grounded=True,
        )