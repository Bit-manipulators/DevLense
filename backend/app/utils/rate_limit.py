from __future__ import annotations

import time
from collections import defaultdict, deque


class InMemoryRateLimiter:
    """Small swappable limiter for an MVP; replace with Redis for multi-instance deploys."""

    def __init__(self, limit: int, window_seconds: int = 60, cleanup_interval_seconds: float = 60.0):
        self.limit = limit
        self.window_seconds = window_seconds
        self.cleanup_interval_seconds = cleanup_interval_seconds
        self._last_cleanup = time.monotonic()
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def _cleanup_stale(self, now: float) -> None:
        cutoff = now - self.window_seconds
        stale_keys = [k for k, dq in self._hits.items() if not dq or dq[-1] <= cutoff]
        for k in stale_keys:
            del self._hits[k]
        self._last_cleanup = now

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        if now - self._last_cleanup > self.cleanup_interval_seconds:
            self._cleanup_stale(now)

        entries = self._hits[key]
        cutoff = now - self.window_seconds
        while entries and entries[0] <= cutoff:
            entries.popleft()
        if len(entries) >= self.limit:
            return False
        entries.append(now)
        return True

