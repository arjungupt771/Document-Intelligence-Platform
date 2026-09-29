from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.observability.context import get_request_id, new_request_id, set_request_id
from app.observability.logging import get_logger, log_with_fields
from app.observability.metrics import ERROR_TOTAL

logger = get_logger("app.request")

REQUEST_ID_HEADER = "X-Request-ID"


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """Assigns/propagates a request id, times the request, and logs a structured access line either way."""

    async def dispatch(self, request: Request, call_next):
        incoming = request.headers.get(REQUEST_ID_HEADER)
        request_id = incoming or new_request_id()
        set_request_id(request_id)

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            ERROR_TOTAL.labels(component="http", exception_type=type(exc).__name__).inc()
            log_with_fields(
                logger, 40, "request_failed",
                method=request.method, path=request.url.path, duration_ms=duration_ms,
            )
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers[REQUEST_ID_HEADER] = request_id
        log_with_fields(
            logger, 20, "request_completed",
            method=request.method, path=request.url.path,
            status_code=response.status_code, duration_ms=duration_ms,
        )
        return response