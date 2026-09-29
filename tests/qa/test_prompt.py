from app.qa.context import GroundingContext
from app.qa.models import AnswerSource
from app.qa.prompt import GroundedPromptBuilder


def test_prompt_contains_user_query():
    context = GroundingContext(
        query="What is the invoice total?",
    )

    prompt = GroundedPromptBuilder().build(context)

    assert "What is the invoice total?" in prompt


def test_prompt_contains_evidence():
    context = GroundingContext(
        query="What is the invoice total?",
        sources=[
            AnswerSource(
                document_id="doc-1",
                document_type="invoice",
                text="Total amount: 12000",
            )
        ],
    )

    prompt = GroundedPromptBuilder().build(context)

    assert "Total amount: 12000" in prompt


def test_prompt_contains_grounding_rules():
    context = GroundingContext(
        query="What is the invoice total?",
    )

    prompt = GroundedPromptBuilder().build(context)

    assert "Do not invent" in prompt
    assert "provided evidence" in prompt
    assert "source of truth" in prompt


def test_empty_context_still_builds_prompt():
    context = GroundingContext(
        query="What is the invoice total?",
    )

    prompt = GroundedPromptBuilder().build(context)

    assert "What is the invoice total?" in prompt
    assert "Evidence:" in prompt

def test_empty_context_explicitly_states_no_evidence():
    context = GroundingContext(
        query="What is the invoice total?",
    )

    prompt = GroundedPromptBuilder().build(context)

    assert "No evidence was retrieved for this question." in prompt