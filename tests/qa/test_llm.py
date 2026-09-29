import pytest

from app.qa.llm import LLMClient


def test_llm_client_is_abstract():
    with pytest.raises(TypeError):
        LLMClient()


class FakeLLMClient(LLMClient):
    def generate(self, prompt: str) -> str:
        return f"Generated: {prompt}"


def test_fake_llm_client_generates_text():
    client = FakeLLMClient()

    result = client.generate("What is the invoice total?")

    assert result == "Generated: What is the invoice total?"