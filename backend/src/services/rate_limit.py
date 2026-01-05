"""
Redis-backed rate limiter.
"""
from __future__ import annotations
from fastapi import Request
from ..core.redis import redis_client

class RateLimiter:
    def __init__(self) -> None:
        self.redis = redis_client

    async def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        redis_key = f"rate_limit:{key}"
        
        try:
            current = await self.redis.incr(redis_key)
            if current == 1:
                await self.redis.expire(redis_key, window_seconds)
            
            return current <= limit
        except Exception as e:
            # If Redis fails, fail open or closed? 
            # Usually fail open (allow) to avoid downtime, or log error.
            print(f"Rate limit error: {e}")
            return True

    async def check_rate_limit(self, request: Request, user_id: str | None = None) -> None:
        """
        Enforce rate limits based on user type.
        - Authenticated Users: Higher limits (e.g., 1000 requests/hour)
        - Guests: Stricter limits (e.g., 50 requests/hour) by IP
        """
        from fastapi import HTTPException
        
        if user_id:
            # Authenticated user limit
            key = f"user:{user_id}"
            limit = 1000
            window = 3600
        else:
            # Guest limit by IP
            ip = request.client.host if request.client else "unknown"
            key = f"guest:{ip}"
            limit = 50
            window = 3600
            
        allowed = await self.allow(key, limit, window)
        if not allowed:
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Please sign up for higher limits.")

# Global singleton
_rate_limiter = RateLimiter()

def get_rate_limiter() -> RateLimiter:
    return _rate_limiter