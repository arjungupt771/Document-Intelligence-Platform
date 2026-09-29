import json

import httpx

from app.qa.config import LLMSettings
from app.qa.errors import (
    LLMConnectionError,
    LLMResponseError,
    LLMTimeoutError,
)
from app.qa.groq_llm import GroqLLMClient


def make_settings():
    return LLMSettings(
        url="https://api.groq.com/openai/v1",
        endpoint="/chat/completions",
        model="openai/gpt-oss-120b",
        timeout=30.0,
        api_key="test-api-key",
    )


def test_groq_client_translates_connection_error():
    def handler(request):
        raise httpx.ConnectError("connection refused")

    client = GroqLLMClient(
        settings=make_settings(),
        transport=httpx.MockTransport(handler),
    )

    try:
        client.generate("test")
        assert False, "Expected LLMConnectionError"
    except LLMConnectionError as exc:
        assert "could not be reached" in str(exc)


def test_groq_client_translates_timeout_error():
    def handler(request):
        raise httpx.ReadTimeout("timed out")

    client = GroqLLMClient(
        settings=make_settings(),
        transport=httpx.MockTransport(handler),
    )

    try:
        client.generate("test")
        assert False, "Expected LLMTimeoutError"
    except LLMTimeoutError as exc:
        assert "timed out" in str(exc)


def test_groq_client_translates_http_error():
    def handler(request):
        return httpx.Response(
            500,
            json={"error": {"message": "model unavailable"}},
        )

    client = GroqLLMClient(
        settings=make_settings(),
        transport=httpx.MockTransport(handler),
    )

    try:
        client.generate("test")
        assert False, "Expected LLMResponseError"
    except LLMResponseError as exc:
        assert "HTTP 500" in str(exc)


def test_groq_client_rejects_invalid_json():
    def handler(request):
        return httpx.Response(
            200,
            content=b"not-json",
        )

    client = GroqLLMClient(
        settings=make_settings(),
        transport=httpx.MockTransport(handler),
    )

    try:
        client.generate("test")
        assert False, "Expected LLMResponseError"
    except LLMResponseError as exc:
        assert "invalid JSON" in str(exc)


def test_groq_client_rejects_missing_response():
    def handler(request):
        return httpx.Response(
            200,
            json={"model": "openai/gpt-oss-120b"},
        )

    client = GroqLLMClient(
        settings=make_settings(),
        transport=httpx.MockTransport(handler),
    )

    try:
        client.generate("test")
        assert False, "Expected LLMResponseError"
    except LLMResponseError as exc:
        assert "valid answer" in str(exc)


def test_groq_client_rejects_empty_response():
    def handler(request):
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": "   "
                        }
                    }
                ]
            },
        )

    client = GroqLLMClient(
        settings=make_settings(),
        transport=httpx.MockTransport(handler),
    )

    try:
        client.generate("test")
        assert False, "Expected LLMResponseError"
    except LLMResponseError as exc:
        assert "valid answer" in str(exc)


def test_groq_client_sends_model_prompt_and_authentication():
    captured = {}

    def handler(request):
        captured["request"] = request

        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": "The invoice total is ₹12,000."
                        }
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)

    settings = make_settings()

    client = GroqLLMClient(
        settings=settings,
        transport=transport,
    )

    result = client.generate("What is the invoice total?")

    assert result == "The invoice total is ₹12,000."

    request = captured["request"]

    assert request.method == "POST"
    assert str(request.url) == (
        "https://api.groq.com/openai/v1/chat/completions"
    )

    assert request.headers["Authorization"] == "Bearer test-api-key"

    assert json.loads(request.content) == {
        "model": "openai/gpt-oss-120b",
        "messages": [
            {
                "role": "user",
                "content": "What is the invoice total?",
            }
        ],
    }


def test_groq_client_raises_for_http_error():
    def handler(request):
        return httpx.Response(
            500,
            json={
                "error": {
                    "message": "model unavailable"
                }
            },
        )

    transport = httpx.MockTransport(handler)

    client = GroqLLMClient(
        settings=make_settings(),
        transport=transport,
    )

    try:
        client.generate("test")
        assert False, "Expected LLMResponseError"
    except LLMResponseError as exc:
        assert "HTTP 500" in str(exc)


def test_groq_client_uses_configured_model():
    captured = {}

    def handler(request):
        captured["request"] = request

        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": "Generated answer"
                        }
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)

    settings = LLMSettings(
        url="https://api.groq.com/openai/v1",
        endpoint="/chat/completions",
        model="custom-model",
        timeout=60.0,
        api_key="test-api-key",
    )

    client = GroqLLMClient(
        settings=settings,
        transport=transport,
    )

    client.generate("test")

    body = json.loads(captured["request"].content)

    assert body["model"] == "custom-model"