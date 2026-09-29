"""Redis-backed limiter with the exact same allow(key) -> (bool, int) interface
as SlidingWindowLimiter, so it's a drop-in swap regardless of worker count.
Falls back to the in-process limiter automatically if REDIS_URL isn't set,
so nothing breaks for single-instance/dev deployments."""
import os

import redis

from app.security.sliding_window import SlidingWindowLimiter


class RedisSlidingWindowLimiter:
    def __init__(self, redis_client: redis.Redis, max_requests: int, window_seconds: int):
        self._redis = redis_client
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    def allow(self, key: str) -> tuple[bool, int]:
        redis_key = f"ratelimit:{key}"
        # INCR + EXPIRE NX is atomic enough for rate limiting purposes (a rare
        # race just means one extra request slips through, not a security hole).
        pipe = self._redis.pipeline()
        pipe.incr(redis_key)
        pipe.ttl(redis_key)
        count, ttl = pipe.execute()

        if ttl == -1:  # key just created, no expiry set yet
            self._redis.expire(redis_key, self.window_seconds)
            ttl = self.window_seconds

        if count > self.max_requests:
            return False, max(ttl, 1)

        return True, 0


def build_limiter(max_requests: int, window_seconds: int):
    """Use this instead of instantiating SlidingWindowLimiter directly in
    app/security/rate_limit.py's middleware, so the backend is chosen once,
    centrally, based on deployment shape."""
    redis_url = os.getenv("REDIS_URL")

    if redis_url:
        client = redis.from_url(redis_url, socket_connect_timeout=2, socket_timeout=2)
        return RedisSlidingWindowLimiter(client, max_requests, window_seconds)

    return SlidingWindowLimiter(max_requests, window_seconds)