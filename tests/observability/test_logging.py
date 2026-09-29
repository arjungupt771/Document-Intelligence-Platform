import json
import logging

from app.observability.context import set_request_id
from app.observability.logging import JSONFormatter


def test_formats_valid_json_with_request_id():
    set_request_id("req-123")
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname=__file__, lineno=1,
        msg="something happened", args=(), exc_info=None,
    )

    payload = json.loads(formatter.format(record))

    assert payload["message"] == "something happened"
    assert payload["level"] == "INFO"
    assert payload["request_id"] == "req-123"


def test_includes_extra_fields():
    set_request_id(None)
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test", level=logging.WARNING, pathname=__file__, lineno=1,
        msg="slow request", args=(), exc_info=None,
    )
    record.extra_fields = {"duration_ms": 42}

    payload = json.loads(formatter.format(record))

    assert payload["duration_ms"] == 42