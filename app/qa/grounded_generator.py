from app.qa.context import GroundingContextLike
from app.qa.generator import AnswerGenerator
from app.qa.llm import LLMClient
from app.qa.models import AnswerResponse
from app.qa.prompt import GroundedPromptBuilder

INSUFFICIENT_EVIDENCE_ANSWER = (
    "I don't have enough evidence in the provided document to answer that question."
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
