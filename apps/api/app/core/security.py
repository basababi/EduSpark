from datetime import datetime, timedelta, timezone
from typing import Literal, Optional
from uuid import uuid4

from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ValidationError

from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

BEARER_TOKEN_TYPE = "bearer"
ACCESS_TOKEN_KIND = "access"
REFRESH_TOKEN_KIND = "refresh"


class TokenClaims(BaseModel):
    sub: str
    type: Literal["access", "refresh"]
    exp: int
    iat: int
    jti: str | None = None
    sid: str | None = None


class TokenValidationError(Exception):
    def __init__(self, detail: str = "Invalid token"):
        super().__init__(detail)
        self.detail = detail


class TokenExpiredError(TokenValidationError):
    def __init__(self, detail: str = "Token expired"):
        super().__init__(detail)


def _create_token(
    *,
    subject: str,
    token_kind: Literal["access", "refresh"],
    expires_minutes: int,
    session_id: str | None = None,
    token_id: str | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=expires_minutes)
    to_encode = {
        "sub": subject,
        "type": token_kind,
        "iat": int(now.timestamp()),
        "exp": expire,
    }
    if session_id:
        to_encode["sid"] = session_id
    if token_id:
        to_encode["jti"] = token_id
    return jwt.encode(
        to_encode,
        settings.jwt_secret_value,
        algorithm=settings.access_token_algorithm,
    )


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    return _create_token(
        subject=subject,
        token_kind=ACCESS_TOKEN_KIND,
        expires_minutes=expires_minutes or settings.access_token_expires_minutes,
    )


def create_refresh_token(
    subject: str,
    *,
    session_id: str,
    token_id: str | None = None,
    expires_minutes: int | None = None,
) -> str:
    return _create_token(
        subject=subject,
        token_kind=REFRESH_TOKEN_KIND,
        expires_minutes=expires_minutes or settings.refresh_token_expires_minutes,
        session_id=session_id,
        token_id=token_id or str(uuid4()),
    )


def create_token(subject: str, expires_minutes: int) -> str:
    return create_access_token(subject=subject, expires_minutes=expires_minutes)


def decode_token_claims(token: str, expected_type: str | None = None) -> TokenClaims:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_value,
            algorithms=[settings.access_token_algorithm],
        )
    except ExpiredSignatureError as exc:
        raise TokenExpiredError("Token expired") from exc
    except JWTError as exc:
        raise TokenValidationError("Invalid token") from exc

    try:
        claims = TokenClaims.model_validate(payload)
    except ValidationError as exc:
        raise TokenValidationError("Invalid token payload") from exc

    if expected_type and claims.type != expected_type:
        raise TokenValidationError("Invalid token type")

    if claims.type == REFRESH_TOKEN_KIND and (not claims.jti or not claims.sid):
        raise TokenValidationError("Refresh token is missing session claims")

    return claims


def verify_token(token: str) -> Optional[str]:
    try:
        return decode_token_claims(token, expected_type=ACCESS_TOKEN_KIND).sub
    except TokenValidationError:
        return None


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)
