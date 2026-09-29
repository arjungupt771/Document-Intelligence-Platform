from app.qa.context import GroundingContext
from app.qa.grounded_generator import GroundedAnswerGenerator, INSUFFICIENT_EVIDENCE_ANSWER
from app.qa.llm import LLMClient
from app.qa.models import AnswerSource


class FakeLLMClient(LLMClient):
    def __init__(self):
        self.last_prompt = None

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return "The invoice total is ₹12,000."


def test_grounded_generator_calls_llm_with_grounded_prompt():
    client = FakeLLMClient()
    generator = GroundedAnswerGenerator(client)

    context = GroundingContext(
        query="What is the invoice total?",
        sources=[
            AnswerSource(
                document_id="doc-1",
                document_type="invoice",
                text="The total invoice amount is ₹12,000.",
                page_number=1,
                score=0.95,
            )
        ],
    )

    result = generator.generate(context)

    assert result.query == "What is the invoice total?"
    assert result.answer == "The invoice total is ₹12,000."
    assert result.grounded is True
    assert len(result.sources) == 1

    assert client.last_prompt is not None
    assert "What is the invoice total?" in client.last_prompt
    assert "The total invoice amount is ₹12,000." in client.last_prompt


def test_grounded_generator_refuses_to_answer_without_evidence():
    client = FakeLLMClient()
    generator = GroundedAnswerGenerator(client)

    context = GroundingContext(query="What is the invoice total?")

    result = generator.generate(context)

    assert result.answer == INSUFFICIENT_EVIDENCE_ANSWER
    assert "₹" not in result.answer
    assert result.sources == []
    assert result.grounded is False
    assert client.last_prompt is None 