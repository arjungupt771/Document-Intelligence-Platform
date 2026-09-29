import time

import httpx

from app.observability.metrics import LLM_ERROR_TOTAL, LLM_LATENCY, LLM_TOKENS_TOTAL, estimate_tokens
from app.qa.config import LLMSettings
from app.qa.errors import LLMConnectionError, LLMResponseError, LLMTimeoutError
from app.qa.llm import LLMClient


class GroqLLMClient(LLMClient):
    """LLM client for Groq's OpenAI-compatible chat completions API."""

    def __init__(self, settings: LLMSettings, transport=None):
        if not settings.api_key:
            raise ValueError("LLM_API_KEY must be set to use GroqLLMClient")
        self._settings = settings
        self._client = httpx.Client(timeout=settings.timeout, transport=transport)

    def generate(self, prompt: str) -> str:
        start = time.perf_counter()
        try:
            response = self._client.post(
                f"{self._settings.url.rstrip('/')}{self._settings.endpoint}",
                headers={"Authorization": f"Bearer {self._settings.api_key}"},
                json={
                    "model": self._settings.model,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
        except httpx.TimeoutException as exc:
            LLM_ERROR_TOTAL.labels(error_type="timeout").inc()
            raise LLMTimeoutError("The LLM provider request timed out.") from exc
        except httpx.RequestError as exc:
            LLM_ERROR_TOTAL.labels(error_type="connection").inc()
            raise LLMConnectionError("The LLM provider could not be reached.") from exc
        finally:
            LLM_LATENCY.observe(time.perf_counter() - start)

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            LLM_ERROR_TOTAL.labels(error_type="http_status").inc()
            raise LLMResponseError(f"The LLM provider returned HTTP {response.status_code}.") from exc

        try:
            data = response.json()
        except ValueError as exc:
            LLM_ERROR_TOTAL.labels(error_type="invalid_json").inc()
            raise LLMResponseError("The LLM provider returned invalid JSON.") from exc

        try:
            answer = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            LLM_ERROR_TOTAL.labels(error_type="empty_answer").inc()
            raise LLMResponseError("The LLM provider response does not contain a valid answer.") from exc

        if not isinstance(answer, str) or not answer.strip():
            LLM_ERROR_TOTAL.labels(error_type="empty_answer").inc()
            raise LLMResponseError("The LLM provider response does not contain a valid answer.")

        LLM_TOKENS_TOTAL.inc(estimate_tokens(prompt) + estimate_tokens(answer))
        return answer