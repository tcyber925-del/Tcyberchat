import redis.asyncio as redis
from .config import settings

# Create a global Redis client
# decode_responses=True ensures we get strings back, not bytes
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
