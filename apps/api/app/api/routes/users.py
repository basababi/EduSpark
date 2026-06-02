from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User
from app.schemas import (
    UserPreferencesRead,
    UserPreferencesUpdate,
    UserProfileRead,
    UserProfileUpdate,
)
from app.services.user_settings_service import (
    get_my_preferences,
    get_my_profile,
    update_my_preferences,
    update_my_profile,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/profile", response_model=UserProfileRead)
async def read_my_profile(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await get_my_profile(db, user)


@router.patch("/me/profile", response_model=UserProfileRead)
async def patch_my_profile(
    payload: UserProfileUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await update_my_profile(db, user, payload)


@router.get("/me/preferences", response_model=UserPreferencesRead)
async def read_my_preferences(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await get_my_preferences(db, user)


@router.patch("/me/preferences", response_model=UserPreferencesRead)
async def patch_my_preferences(
    payload: UserPreferencesUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await update_my_preferences(db, user, payload)
