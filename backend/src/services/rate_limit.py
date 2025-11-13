"""
Simple in-memory rate limiter with per-key sliding window.
Not suitable for multi-process without external store.
"""
from __future__ import annotations

import asyncio
import time
from collections import deque
from typing import Deque, Dict


class RateLimiter:
    def __init__(self) -> None:
        # key -> deque[timestamps]
        self._buckets: Dict[str, Deque[float]] = {}
        self._lock = asyncio.Lock()

    async def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.time()
        window_start = now - window_seconds
        async with self._lock:
            q = self._buckets.get(key)
            if q is None:
                q = deque()
                self._buckets[key] = q
            # drop expired
            while q and q[0] < window_start:
                q.popleft()
            if len(q) >= limit:
                return False
            q.append(now)
            return True


# Global singleton
_rate_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
