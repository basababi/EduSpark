from functools import lru_cache

from redis.asyncio import Redis, from_url

from app.core.config import settings


@lru_cache
def get_redis_client() -> Redis:
    return from_url(settings.redis_url, encoding="utf-8", decode_responses=True)


async def close_redis_client() -> None:
    if get_redis_client.cache_info().currsize == 0:
        return
    client = get_redis_client()
    if hasattr(client, "aclose"):
        await client.aclose()
    else:
        await client.close()
    get_redis_client.cache_clear()
