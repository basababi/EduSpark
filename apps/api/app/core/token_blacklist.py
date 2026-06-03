"""Token blacklist management for access token revocation on logout."""
from datetime import datetime, timezone
from app.db.redis import get_redis_client
from app.core.security import decode_token_claims, TokenValidationError

BLACKLIST_PREFIX = "auth:blacklist:access"


async def blacklist_access_token(token: str) -> None:
    """Blacklist an access token on logout (immediate revocation)."""
    try:
        claims = decode_token_claims(token, expected_type="access")
    except TokenValidationError:
        return

    redis = get_redis_client()
    key = f"{BLACKLIST_PREFIX}:{claims.jti or claims.sub}"
    ttl = int(
        (
            datetime.fromtimestamp(claims.exp, tz=timezone.utc)
            - datetime.now(timezone.utc)
        ).total_seconds()
    )
    ttl = max(ttl, 1)
    await redis.set(key, "1", ex=ttl)


async def is_access_token_blacklisted(token: str) -> bool:
    """Check if an access token has been blacklisted."""
    try:
        claims = decode_token_claims(token, expected_type="access")
    except TokenValidationError:
        return False

    redis = get_redis_client()
    key = f"{BLACKLIST_PREFIX}:{claims.jti or claims.sub}"
    exists = await redis.exists(key)
    return exists > 0
