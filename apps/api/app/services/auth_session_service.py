from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.config import settings
from app.db.redis import get_redis_client
from app.schemas import RefreshSessionState, Token
from app.services.auth_service import get_active_user_by_id

REFRESH_SESSION_PREFIX = "auth:refresh"


class AuthSessionError(Exception):
    def __init__(self, detail: str, code: str = "invalid"):
        super().__init__(detail)
        self.detail = detail
        self.code = code


class AuthSessionStoreError(AuthSessionError):
    def __init__(self, detail: str = "Authentication session store unavailable"):
        super().__init__(detail=detail, code="unavailable")


def _session_key(session_id: str) -> str:
    return f"{REFRESH_SESSION_PREFIX}:{session_id}"


def _refresh_ttl_seconds() -> int:
    return settings.refresh_token_expires_minutes * 60


async def _save_session(state: RefreshSessionState, ttl_seconds: int | None = None) -> None:
    try:
        redis = get_redis_client()
        await redis.set(
            _session_key(state.session_id),
            state.model_dump_json(),
            ex=ttl_seconds or _refresh_ttl_seconds(),
        )
    except Exception as exc:
        raise AuthSessionStoreError() from exc


async def _load_session(session_id: str) -> RefreshSessionState | None:
    try:
        redis = get_redis_client()
        payload = await redis.get(_session_key(session_id))
    except Exception as exc:
        raise AuthSessionStoreError() from exc
    if payload is None:
        return None
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")
    return RefreshSessionState.model_validate_json(payload)


async def _revoke_session(
    session_id: str,
    *,
    user_id: str,
    current_jti: str,
    reason: str,
    ttl_seconds: int | None = None,
) -> None:
    state = RefreshSessionState(
        user_id=user_id,
        session_id=session_id,
        current_jti=current_jti,
        revoked=True,
        revoke_reason=reason,
        revoked_at=datetime.now(timezone.utc),
    )
    await _save_session(state, ttl_seconds=ttl_seconds)


def _ttl_from_claims(claims: security.TokenClaims) -> int:
    expires_at = datetime.fromtimestamp(claims.exp, tz=timezone.utc)
    remaining = int((expires_at - datetime.now(timezone.utc)).total_seconds())
    return max(remaining, 1)


async def issue_token_pair(user_id: str) -> Token:
    session_id = str(uuid4())
    refresh_jti = str(uuid4())
    access_token = security.create_access_token(user_id)
    refresh_token = security.create_refresh_token(
        user_id,
        session_id=session_id,
        token_id=refresh_jti,
    )

    state = RefreshSessionState(
        user_id=user_id,
        session_id=session_id,
        current_jti=refresh_jti,
    )
    await _save_session(state)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type=security.BEARER_TOKEN_TYPE,
    )


async def refresh_token_pair(db: AsyncSession, refresh_token: str) -> Token:
    try:
        claims = security.decode_token_claims(
            refresh_token,
            expected_type=security.REFRESH_TOKEN_KIND,
        )
    except security.TokenExpiredError as exc:
        raise AuthSessionError("Refresh token expired", code="expired") from exc
    except security.TokenValidationError as exc:
        raise AuthSessionError("Invalid refresh token", code="invalid") from exc

    session = await _load_session(claims.sid)
    if session is None:
        raise AuthSessionError("Invalid refresh token", code="invalid")
    if session.revoked:
        raise AuthSessionError("Refresh token has been revoked", code="revoked")
    if session.user_id != claims.sub or session.current_jti != claims.jti:
        await _revoke_session(
            session.session_id,
            user_id=session.user_id,
            current_jti=session.current_jti,
            reason="refresh_token_reuse_detected",
        )
        raise AuthSessionError("Refresh token has been revoked", code="revoked")

    user = await get_active_user_by_id(db, claims.sub)
    if not user:
        await _revoke_session(
            session.session_id,
            user_id=session.user_id,
            current_jti=session.current_jti,
            reason="user_not_active",
        )
        raise AuthSessionError("User is no longer active", code="invalid")

    new_refresh_jti = str(uuid4())
    access_token = security.create_access_token(str(user.id))
    rotated_refresh_token = security.create_refresh_token(
        str(user.id),
        session_id=session.session_id,
        token_id=new_refresh_jti,
    )

    session.current_jti = new_refresh_jti
    session.rotated_at = datetime.now(timezone.utc)
    session.revoked = False
    session.revoke_reason = None
    session.revoked_at = None
    await _save_session(session)

    return Token(
        access_token=access_token,
        refresh_token=rotated_refresh_token,
        token_type=security.BEARER_TOKEN_TYPE,
    )


async def revoke_refresh_token(refresh_token: str) -> None:
    try:
        claims = security.decode_token_claims(
            refresh_token,
            expected_type=security.REFRESH_TOKEN_KIND,
        )
    except security.TokenExpiredError:
        return
    except security.TokenValidationError as exc:
        raise AuthSessionError("Invalid refresh token", code="invalid") from exc

    session = await _load_session(claims.sid)
    if session is None:
        await _revoke_session(
            claims.sid,
            user_id=claims.sub,
            current_jti=claims.jti,
            reason="logout",
            ttl_seconds=_ttl_from_claims(claims),
        )
        return

    await _revoke_session(
        session.session_id,
        user_id=session.user_id,
        current_jti=session.current_jti,
        reason="logout",
        ttl_seconds=_ttl_from_claims(claims),
    )
