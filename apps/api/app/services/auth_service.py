import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload

from app.models import User, Role, Profile
from app.schemas import UserCreate
from app.core import security


async def get_role(db: AsyncSession, name: str) -> Role:
    res = await db.execute(select(Role).where(Role.name == name))
    role = res.scalar_one_or_none()
    if role:
        return role
    role = Role(name=name, description=f"Default {name} role")
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role


async def create_user(db: AsyncSession, payload: UserCreate) -> User:
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    student_role = await get_role(db, "student")
    user = User(
        email=payload.email,
        hashed_password=security.hash_password(payload.password),
        role_id=student_role.id,
    )
    db.add(user)
    await db.flush()
    profile = Profile(user_id=user.id, full_name=payload.full_name)
    db.add(profile)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    res = await db.execute(select(User).where(User.email == email))
    user = res.scalar_one_or_none()
    if not user:
        return None
    if not user.is_active:
        return None
    if not security.verify_password(password, user.hashed_password):
        return None
    return user


async def get_active_user_by_id(db: AsyncSession, user_id: str | uuid.UUID) -> User | None:
    resolved_user_id = uuid.UUID(str(user_id))
    result = await db.execute(
        select(User)
        .options(selectinload(User.profile), selectinload(User.role))
        .where(User.id == resolved_user_id, User.is_active.is_(True))
    )
    return result.scalar_one_or_none()
