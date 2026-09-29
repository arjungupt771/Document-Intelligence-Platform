import os
from dataclasses import dataclass, field
from typing import Optional

from app.security.ssrf_guard import SSRFValidationError, validate_allowlisted_https_url

DEFAULT_ALLOWED_LLM_HOSTS = ("api.groq.com",)

# Environments where an unusable / unsafe LLM configuration must stop the app.
_STRICT_ENVIRONMENTS = {"production", "staging"}


def _is_strict_environment() -> bool:
    return os.getenv("APP_ENV", "development").strip().lower() in _STRICT_ENVIRONMENTS


def _allowed_hosts() -> tuple[str, ...]:
    raw = os.getenv("LLM_ALLOWED_HOSTS", "")
    hosts = tuple(h.strip().lower() for h in raw.split(",") if h.strip())
    return hosts or DEFAULT_ALLOWED_LLM_HOSTS


@dataclass(frozen=True)
class LLMSettings:
    """Configuration for the document QA language model (Groq, OpenAI-compatible)."""

    url: str
    endpoint: str
    model: str
    timeout: float
    api_key: Optional[str] = field(repr=False)

    @classmethod
    def from_env(cls) -> "LLMSettings":
        url = os.getenv("LLM_URL", "https://api.groq.com/openai/v1")
        endpoint = os.getenv("LLM_ENDPOINT", "/chat/completions")
        model = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")

        try:
            timeout = float(os.getenv("LLM_TIMEOUT", "30.0"))
        except ValueError as exc:
            raise ValueError("LLM_TIMEOUT must be a number") from exc

        api_key = (os.getenv("LLM_API_KEY") or "").strip() or None

        if not url.strip():
            raise ValueError("LLM_URL must not be empty")

        if not endpoint.strip():
            raise ValueError("LLM_ENDPOINT must not be empty")

        if not endpoint.startswith("/"):
            raise ValueError("LLM_ENDPOINT must start with '/'")

        if not model.strip():
            raise ValueError("LLM_MODEL must not be empty")

        if timeout <= 0:
            raise ValueError("LLM_TIMEOUT must be greater than 0")

        if _is_strict_environment():
            # HTTPS validation -> SSRF protection -> allowed external host.
            try:
                validate_allowlisted_https_url(url, _allowed_hosts())
            except SSRFValidationError as exc:
                raise ValueError(f"LLM_URL is not permitted: {exc}") from exc

            if api_key is None:
                raise ValueError("LLM_API_KEY must be set when APP_ENV is production or staging")

        return cls(
            url=url,
            endpoint=endpoint,
            model=model,
            timeout=timeout,
            api_key=api_key,
        )


def validate_llm_config() -> None:
    """Call once at process startup so an unusable LLM configuration in
    production refuses to boot instead of failing on the first request."""
    LLMSettings.from_env()