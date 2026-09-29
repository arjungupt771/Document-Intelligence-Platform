import os

import pytest

from app.qa.config import LLMSettings
from app.qa.groq_llm import GroqLLMClient


@pytest.mark.integration
def test_real_groq_generation():
    api_key = os.getenv("LLM_API_KEY")

    if not api_key:
        pytest.skip("LLM_API_KEY is not configured")

    settings = LLMSettings(
        url=os.getenv(
            "LLM_URL",
            "https://api.groq.com/openai/v1",
        ),
        endpoint=os.getenv(
            "LLM_ENDPOINT",
            "/chat/completions",
        ),
        model=os.getenv(
            "LLM_MODEL",
            "openai/gpt-oss-120b",
        ),
        timeout=float(os.getenv("LLM_TIMEOUT", "60.0")),
        api_key=api_key,
    )

    client = GroqLLMClient(settings=settings)

    prompt = """
Answer using only the evidence below.

Question:
What is the invoice total?

Evidence:
The invoice total is ₹12,000.
"""

    answer = client.generate(prompt)

    assert isinstance(answer, str)
    assert answer.strip()