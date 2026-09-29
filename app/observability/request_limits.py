from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


MAX_REQUEST_BODY_SIZE = 12 * 1024 * 1024


class RequestBodyLimitMiddleware(BaseHTTPMiddleware):
    """Reject HTTP requests whose declared body exceeds the configured limit."""

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")

        if content_length is not None:
            try:
                request_size = int(content_length)
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid Content-Length header"},
                )

            if request_size > MAX_REQUEST_BODY_SIZE:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "Request body is too large"},
                )

        return await call_next(request)