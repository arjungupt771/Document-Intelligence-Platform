from app.qa.context import GroundingContext
from app.qa.generator import AnswerGenerator
from app.qa.models import AnswerResponse


class DeterministicAnswerGenerator(AnswerGenerator):
    def generate(
        self,
        context: GroundingContext,
    ) -> AnswerResponse:
        if context.is_empty:
            return AnswerResponse(
                query=context.query,
                answer=(
                    "The available documents do not contain enough "
                    "information to answer this question."
                ),
                grounded=False,
            )

        return AnswerResponse(
            query=context.query,
            answer=context.sources[0].text,
            sources=context.sources,
            grounded=True,
        )
