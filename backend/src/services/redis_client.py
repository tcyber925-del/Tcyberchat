"""
Optional Redis client helper. Returns a redis client if REDIS_URL is set and redis is installed.
"""
from __future__ import annotations

import os
from typing import Any, Optional

_redis_client: Any | None = None


def get_redis() -> Optional[Any]:
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    url = os.getenv("REDIS_URL")
    if not url:
        return None
    try:
        import redis  # type: ignore

        _redis_client = redis.Redis.from_url(url, decode_responses=True)
        # quick ping
        _redis_client.ping()
        return _redis_client
    except Exception:
        return None
