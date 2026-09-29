"""In-process sliding-window rate limiter."""

import time
from collections import defaultdict, deque


class SlidingWindowLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque] = defaultdict(deque)

    def allow(self, key: str) -> tuple[bool, int]:
        now = time.monotonic()
        window_start = now - self.window_seconds
        hits = self._hits[key]

        while hits and hits[0] < window_start:
            hits.popleft()

        if len(hits) >= self.max_requests:
            retry_after = int(self.window_seconds - (now - hits[0]))
            return False, max(retry_after, 1)

        hits.append(now)
        return True, 0
