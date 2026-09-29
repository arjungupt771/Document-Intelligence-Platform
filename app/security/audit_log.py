"""Structured security-event logging, separate from the general app logger
so security events can be shipped/retained differently (e.g. longer
retention, SIEM ingestion) and are never dropped by log-level filtering.
"""
import logging
import re
from datetime import datetime, timezone
from typing import Any

security_logger = logging.getLogger("security")

# Redact anything that looks like a secret before it ever reaches a log line.
_REDACT_PATTERNS = [
    (re.compile(r"(Bearer\s+)[A-Za-z0-9\-_.]+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"([\"']?password[\"']?\s*[:=]\s*[\"']?)[^\s\"',}]+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"([\"']?api[_-]?key[\"']?\s*[:=]\s*[\"']?)[^\s\"',}]+", re.IGNORECASE), r"\1[REDACTED]"),
]


def redact(text: str) -> str:
    for pattern, replacement in _REDACT_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def log_security_event(
    event_type: str,
    *,
    outcome: str,  # "success" | "denied" | "error"
    request_id: str | None = None,
    client_key: str | None = None,
    resource: str | None = None,
    detail: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """
    event_type examples: "auth.failure", "auth.success", "authz.denied",
    "rate_limit.exceeded", "upload.rejected", "prompt_injection.detected"
    """
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "outcome": outcome,
        "request_id": request_id,
        "client_key": client_key,
        "resource": resource,
        "detail": redact(detail) if detail else None,
    }
    if extra:
        payload.update({k: redact(str(v)) for k, v in extra.items()})

    level = logging.WARNING if outcome != "success" else logging.INFO
    security_logger.log(level, "security_event", extra={"security_event": payload})