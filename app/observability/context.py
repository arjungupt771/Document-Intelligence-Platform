from __future__ import annotations

import contextvars
import uuid

_request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)


def new_request_id() -> str:
    return uuid.uuid4().hex[:16]


def set_request_id(request_id: str) -> None:
    _request_id_var.set(request_id)


def get_request_id() -> str | None:
    return _request_id_var.get()