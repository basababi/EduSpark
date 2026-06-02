from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Profile, User, UserPreference
from app.schemas import (
    UserPreferencesRead,
    UserPreferencesUpdate,
    UserProfileRead,
    UserProfileUpdate,
)


def _normalize_interests(interests: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for interest in interests:
        cleaned = interest.strip()
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(cleaned)
    return normalized


async def _get_or_create_profile(db: AsyncSession, user: User) -> Profile:
    if user.profile:
        return user.profile
    profile = Profile(user_id=user.id)
    db.add(profile)
    await db.flush()
    user.profile = profile
    return profile


async def _get_or_create_preferences(db: AsyncSession, user_id: UUID) -> UserPreference:
    result = await db.execute(select(UserPreference).where(UserPreference.user_id == user_id))
    prefs = result.scalar_one_or_none()
    if prefs:
        return prefs
    prefs = UserPreference(user_id=user_id)
    db.add(prefs)
    await db.flush()
    return prefs


def _build_profile_read(user: User, profile: Profile, prefs: UserPreference) -> UserProfileRead:
    return UserProfileRead(
        name=profile.full_name,
        email=user.email,
        role=user.role.name if user.role else None,
        track=profile.learner_level,
        interests=_normalize_interests(prefs.interests or []),
        avatar_url=profile.avatar_url,
        locale=profile.locale,
        timezone=profile.timezone,
    )


def _build_preferences_read(prefs: UserPreference) -> UserPreferencesRead:
    return UserPreferencesRead(
        email_notifications=prefs.email_notifications,
        weekly_report=prefs.weekly_report,
        daily_reminder=prefs.daily_reminder,
        dark_mode=prefs.dark_mode,
        compact_view=prefs.compact_view,
    )


async def get_my_profile(db: AsyncSession, user: User) -> UserProfileRead:
    profile = await _get_or_create_profile(db, user)
    prefs = await _get_or_create_preferences(db, user.id)
    await db.commit()
    return _build_profile_read(user, profile, prefs)


async def update_my_profile(
    db: AsyncSession,
    user: User,
    payload: UserProfileUpdate,
) -> UserProfileRead:
    profile = await _get_or_create_profile(db, user)
    prefs = await _get_or_create_preferences(db, user.id)

    if payload.email is not None and payload.email != user.email:
        existing = await db.execute(
            select(User.id).where(User.email == payload.email, User.id != user.id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        user.email = payload.email

    if payload.name is not None:
        profile.full_name = payload.name
    if payload.track is not None:
        profile.learner_level = payload.track
    if payload.avatar_url is not None:
        profile.avatar_url = payload.avatar_url
    if payload.locale is not None:
        profile.locale = payload.locale
    if payload.timezone is not None:
        profile.timezone = payload.timezone
    if payload.interests is not None:
        prefs.interests = _normalize_interests(payload.interests)

    await db.commit()
    return _build_profile_read(user, profile, prefs)


async def get_my_preferences(db: AsyncSession, user: User) -> UserPreferencesRead:
    prefs = await _get_or_create_preferences(db, user.id)
    await db.commit()
    return _build_preferences_read(prefs)


async def update_my_preferences(
    db: AsyncSession,
    user: User,
    payload: UserPreferencesUpdate,
) -> UserPreferencesRead:
    prefs = await _get_or_create_preferences(db, user.id)
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(prefs, key, value)
    await db.commit()
    return _build_preferences_read(prefs)
