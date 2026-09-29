import httpx
import json
from app.qa.http_llm import HTTPClientLLM
from app.qa.errors import (
    LLMConnectionError,
    LLMResponseError,
    LLMTimeoutError,
)


def test_http_llm_sends_prompt_and_returns_answer():
    captured = {}

    def handler(request):
        captured["request"] = request

        return httpx.Response(
            200,
            json={
                "answer": "The invoice total is ₹12,000."
            },
        )

    transport = httpx.MockTransport(handler)

    client = HTTPClientLLM(
        base_url="http://localhost:9000",
        transport=transport,
    )

    result = client.generate("What is the invoice total?")

    assert result == "The invoice total is ₹12,000."

    request = captured["request"]

    assert request.method == "POST"
    assert str(request.url) == "http://localhost:9000/generate"

    assert json.loads(request.content) == {
    "prompt": "What is the invoice total?"
    }


def test_http_llm_raises_for_http_error():
    def handler(request):
        return httpx.Response(
            500,
            json={"error": "LLM unavailable"},
        )

    transport = httpx.MockTransport(handler)

    client = HTTPClientLLM(
        base_url="http://localhost:9000",
        transport=transport,
    )

    try:
        client.generate("test")
        assert False, "Expected HTTPStatusError"
    except httpx.HTTPStatusError as exc:
        assert exc.response.status_code == 500


def test_http_llm_supports_custom_endpoint():
    captured = {}

    def handler(request):
        captured["request"] = request

        return httpx.Response(
            200,
            json={"answer": "hello"},
        )

    transport = httpx.MockTransport(handler)

    client = HTTPClientLLM(
        base_url="http://localhost:9000",
        endpoint="/v1/generate",
        transport=transport,
    )

    result = client.generate("hello")

    assert result == "hello"
    assert str(captured["request"].url) == "http://localhost:9000/v1/generate"
