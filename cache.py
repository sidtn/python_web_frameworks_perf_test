from __future__ import annotations

import os

from redis.asyncio import Redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
ORDER_CACHE_TTL = int(os.getenv("ORDER_CACHE_TTL", "0"))
APP_NAME = os.getenv("APP_NAME", "app")
CACHE_PREFIX = os.getenv("CACHE_PREFIX", f"orders:{APP_NAME}")

_redis_client: Redis | None = None


def get_redis() -> Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client


def order_cache_key(order_id: int, lite: bool) -> str:
    suffix = "lite" if lite else "full"
    return f"{CACHE_PREFIX}:{suffix}:{order_id}"


async def get_cached_json(key: str) -> str | None:
    return await get_redis().get(key)


async def set_cached_json(key: str, value: str) -> None:
    if ORDER_CACHE_TTL > 0:
        await get_redis().set(key, value, ex=ORDER_CACHE_TTL)
    else:
        await get_redis().set(key, value)


async def clear_cache() -> None:
    redis = get_redis()
    pattern = f"{CACHE_PREFIX}:*"
    cursor = 0
    keys: list[str] = []
    while True:
        cursor, batch = await redis.scan(cursor=cursor, match=pattern, count=1000)
        keys.extend(batch)
        if cursor == 0:
            break
    if keys:
        await redis.delete(*keys)
