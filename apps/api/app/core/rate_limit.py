"""Per-user rate limiting using sliding window in Redis."""
from datetime import datetime, timezone
from app.db.redis import get_redis_client


async def check_rate_limit(
    user_id: str, limit: int = 1000, window_seconds: int = 60
) -> tuple[bool, int]:
    """Sliding window rate limit. Returns (allowed, remaining)."""
    redis = get_redis_client()
    key = f"ratelimit:{user_id}"
    now = datetime.now(timezone.utc).timestamp()
    window_start = now - window_seconds

    # Remove old entries outside window
    await redis.zremrangebyscore(key, 0, window_start)

    # Count requests in window
    count = await redis.zcard(key)

    if count >= limit:
        return False, 0

    # Add current request
    await redis.zadd(key, {str(now): now})
    await redis.expire(key, window_seconds + 10)

    return True, limit - count - 1
