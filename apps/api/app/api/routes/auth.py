from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db
from app.models import User
from app.schemas import LogoutRequest, RefreshTokenRequest, Token, UserCreate, UserLogin, UserRead
from app.services.auth_service import authenticate_user, create_user
from app.services.auth_session_service import (
    AuthSessionError,
    issue_token_pair,
    refresh_token_pair,
    revoke_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _resolve_refresh_token(
    payload: RefreshTokenRequest | LogoutRequest | None,
    query_token: str | None,
) -> str:
    if payload is not None:
        return payload.refresh_token
    if query_token:
        return query_token
    raise HTTPException(status_code=400, detail="Refresh token is required")


def _raise_session_error(exc: AuthSessionError) -> None:
    http_status = (
        status.HTTP_503_SERVICE_UNAVAILABLE
        if exc.code == "unavailable"
        else status.HTTP_401_UNAUTHORIZED
    )
    raise HTTPException(status_code=http_status, detail=exc.detail) from exc


@router.post("/register", response_model=UserRead, status_code=201)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await create_user(db, payload)
    result = await db.execute(
        select(User)
        .options(selectinload(User.profile), selectinload(User.role))
        .where(User.id == user.id)
    )
    user = result.scalar_one()
    return UserRead(
        id=user.id,
        email=user.email,
        full_name=user.profile.full_name if user.profile else None,
        role=user.role.name if user.role else None,
        created_at=user.created_at,
    )


@router.post("/login", response_model=Token)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect credentials")
    return await issue_token_pair(str(user.id))


@router.post("/refresh", response_model=Token)
async def refresh(
    payload: RefreshTokenRequest | None = Body(default=None),
    token: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    refresh_token = _resolve_refresh_token(payload, token)
    try:
        return await refresh_token_pair(db, refresh_token)
    except AuthSessionError as exc:
        _raise_session_error(exc)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: LogoutRequest | None = Body(default=None),
    token: str | None = Query(default=None),
):
    refresh_token = _resolve_refresh_token(payload, token)
    try:
        await revoke_refresh_token(refresh_token)
    except AuthSessionError as exc:
        _raise_session_error(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserRead)
async def me(user: User = Depends(get_current_user)):
    return UserRead(
        id=user.id,
        email=user.email,
        full_name=user.profile.full_name if user.profile else None,
        role=user.role.name if user.role else None,
        created_at=user.created_at,
    )
