"""Fail-fast validation of required secrets at startup.

Import and call `validate_secrets()` once, early in app/main.py, so a
misconfigured deployment refuses to start instead of running with a
weak or missing credential.
"""
import os
import secrets as _secrets
from urllib.parse import urlsplit

MIN_API_KEY_LENGTH = 32

# Values that must never make it into a running deployment.
_KNOWN_PLACEHOLDER_VALUES = {
    "",
    "changeme",
    "change-me",
    "secret",
    "password",
    "<generate-a-strong-secret>",
}


class InsecureConfigurationError(RuntimeError):
    """Raised when a required secret is missing, weak, or a known placeholder."""


def _check_api_key() -> None:
    api_key = os.getenv("API_AUTH_KEY", "")

    if api_key.strip().lower() in _KNOWN_PLACEHOLDER_VALUES:
        raise InsecureConfigurationError(
            "API_AUTH_KEY is missing or is a placeholder value. "
            "Generate one with `python -c \"import secrets; print(secrets.token_urlsafe(32))\"`."
        )

    if len(api_key) < MIN_API_KEY_LENGTH:
        raise InsecureConfigurationError(
            f"API_AUTH_KEY must be at least {MIN_API_KEY_LENGTH} characters."
        )


def _check_database_url() -> None:
    url = os.getenv("DATABASE_URL", "")

    if not url:
        raise InsecureConfigurationError("DATABASE_URL is not configured.")

    try:
        parsed = urlsplit(url)
    except ValueError as exc:
        raise InsecureConfigurationError(
            "DATABASE_URL is invalid."
        ) from exc

    password = parsed.password or ""

    weak_passwords = {
        "password",
        "postgres",
        "changeme",
    }

    if password.lower() in weak_passwords:
        raise InsecureConfigurationError(
            "DATABASE_URL appears to use a default/weak credential."
        )


def _check_environment_flag() -> str:
    env = os.getenv("APP_ENV", "development").lower()

    if env == "production" and os.getenv("DATABASE_ECHO", "false").lower() == "true":
        raise InsecureConfigurationError(
            "DATABASE_ECHO must not be enabled in production (leaks SQL, possibly PII, to logs)."
        )

    return env


def validate_secrets() -> None:
    """Call at process startup. Raises InsecureConfigurationError to abort boot."""
    env = _check_environment_flag()

    _check_api_key()
    _check_database_url()

    if env == "production" and not os.getenv("QDRANT_API_KEY"):
        # Not fatal by default since local Qdrant behind a private network is common,
        # but surface it loudly.
        import warnings
        warnings.warn(
            "QDRANT_API_KEY is not set while APP_ENV=production. "
            "Confirm Qdrant is not reachable from outside the trusted network.",
            stacklevel=2,
        )


def generate_api_key() -> str:
    """Helper for ops: `python -c 'from app.security.secrets import generate_api_key; print(generate_api_key())'`"""
    return _secrets.token_urlsafe(32)