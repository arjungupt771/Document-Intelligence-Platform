from app.qa.context import GroundingContext
from app.qa.models import AnswerSource
from app.qa.test_generator import DeterministicAnswerGenerator


def test_generator_answers_from_first_source():
    source = AnswerSource(
        document_id="doc-1",
        document_type="invoice",
        text="Total amount: 12000",
        page_number=1,
        score=0.95,
    )

    context = GroundingContext(
        query="What is the invoice total?",
        sources=[source],
    )

    generator = DeterministicAnswerGenerator()

    response = generator.generate(context)

    assert response.query == context.query
    assert response.answer == "Total amount: 12000"
    assert response.sources == [source]
    assert response.grounded is True


def test_generator_handles_missing_evidence():
    context = GroundingContext(
        query="What is the invoice total?",
    )

    generator = DeterministicAnswerGenerator()

    response = generator.generate(context)

    assert response.query == context.query
    assert response.grounded is False
    assert response.sources == []
    assert "not contain enough information" in response.answer