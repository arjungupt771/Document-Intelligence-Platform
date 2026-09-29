from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone

from app.observability.context import get_request_id


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": get_request_id(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        payload.update(getattr(record, "extra_fields", {}))
        return json.dumps(payload)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_with_fields(logger: logging.Logger, level: int, message: str, **fields) -> None:
    """logging.INFO=20, logging.WARNING=30, logging.ERROR=40 -- pass the int directly to avoid importing the constants everywhere this is called."""
    logger.log(level, message, extra={"extra_fields": fields})