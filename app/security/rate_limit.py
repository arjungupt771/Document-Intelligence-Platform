
from app.security.redis_rate_limit import build_limiter
from app.security.sliding_window import SlidingWindowLimiter
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import redis




class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-client-key limiting. Keys by API key when present, else by IP.

    Applies stricter limits to expensive routes (QA, analyst) than to
    cheap ones (health, metrics).
    """

    _DEFAULT = build_limiter(max_requests=120, window_seconds=60)
    _EXPENSIVE = build_limiter(max_requests=20, window_seconds=60)
    _EXPENSIVE_PREFIXES = ("/qa", "/analyst", "/documents")

    def _client_key(self, request: Request) -> str:
        auth = request.headers.get("authorization")
        if auth:
            return f"key:{auth[-16:]}"  # last chars, avoids logging full token
        client = request.client
        return f"ip:{client.host}" if client else "ip:unknown"

    async def dispatch(self, request: Request, call_next):
        if request.url.path in ("/health", "/metrics"):
            return await call_next(request)

        key = self._client_key(request)
        limiter = (
            self._EXPENSIVE
            if request.url.path.startswith(self._EXPENSIVE_PREFIXES)
            else self._DEFAULT
        )
        try:
            allowed, retry_after = limiter.allow(key)
        except redis.RedisError:
            allowed, retry_after = True, 0
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)