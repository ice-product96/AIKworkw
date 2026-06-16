from functools import lru_cache

import redis.asyncio as aioredis

from app.core.config import get_settings


@lru_cache
def get_redis_pool() -> aioredis.Redis:
    settings = get_settings()
    return aioredis.from_url(settings.redis_url, decode_responses=True)


async def close_redis() -> None:
    pool = get_redis_pool()
    await pool.aclose()
    get_redis_pool.cache_clear()
