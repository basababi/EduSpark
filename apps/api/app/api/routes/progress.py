from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User
from app.schemas import (
    ProgressSnapshotRead,
    ProgressSummaryRead,
    StudySessionCreate,
    StudySessionRead,
)
from app.services.progress_service import (
    get_progress_snapshots,
    get_progress_summary,
    record_study_session,
)

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/summary", response_model=ProgressSummaryRead)
async def read_progress_summary(
    days: int = Query(default=7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await get_progress_summary(db, user, days=days)


@router.get("/snapshots", response_model=list[ProgressSnapshotRead])
async def read_progress_snapshots(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await get_progress_snapshots(db, user, limit=limit)


@router.post("/study-sessions", response_model=StudySessionRead, status_code=201)
async def create_study_session(
    payload: StudySessionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await record_study_session(db, user, payload)
