from collections.abc import AsyncGenerator

import redis.asyncio as redis

from config import settings

redis_pool = redis.from_url(settings.redis_url, decode_responses=True)


async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    yield redis_pool
