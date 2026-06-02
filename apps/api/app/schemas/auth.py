import uuid
from datetime import datetime
from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str | None
    role: str | None
    created_at: datetime


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(
        validation_alias=AliasChoices("refresh_token", "token"),
        serialization_alias="refresh_token",
    )


class LogoutRequest(BaseModel):
    refresh_token: str = Field(
        validation_alias=AliasChoices("refresh_token", "token"),
        serialization_alias="refresh_token",
    )


class TokenPayload(BaseModel):
    sub: str | None = None
    type: str | None = None
    jti: str | None = None
    sid: str | None = None


class RefreshSessionState(BaseModel):
    user_id: str
    session_id: str
    current_jti: str
    revoked: bool = False
    revoke_reason: str | None = None
    rotated_at: datetime | None = None
    revoked_at: datetime | None = None
