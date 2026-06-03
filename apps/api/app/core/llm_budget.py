"""LLM usage tracking and budget enforcement."""
from datetime import datetime, timezone
from app.db.redis import get_redis_client

BUDGET_PREFIX = "llm:budget"


async def check_daily_budget(user_id: str, max_messages: int = 20) -> bool:
    """Check if user has exceeded daily message limit."""
    redis = get_redis_client()
    today = datetime.now(timezone.utc).date().isoformat()
    key = f"{BUDGET_PREFIX}:{user_id}:{today}"

    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 86400)

    return count <= max_messages


async def get_user_budget_remaining(user_id: str) -> int:
    """Get remaining messages for today."""
    redis = get_redis_client()
    today = datetime.now(timezone.utc).date().isoformat()
    key = f"{BUDGET_PREFIX}:{user_id}:{today}"

    count = await redis.get(key) or 0
    return max(0, 20 - int(count))


async def log_token_usage(user_id: str, input_tokens: int, output_tokens: int):
    """Track token usage for billing."""
    redis = get_redis_client()
    key = f"tokens:monthly:{user_id}:{datetime.now(timezone.utc).strftime('%Y%m')}"
    await redis.incrby(key, input_tokens + output_tokens)
