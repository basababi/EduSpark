from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User
from app.schemas import LessonDetailRead, ModuleDetailRead, SubjectDetailRead, SubjectSummaryRead
from app.services.learning_service import (
    get_lesson_detail,
    get_subject_detail,
    get_subject_modules,
    list_subjects,
)

router = APIRouter(tags=["learning"])


@router.get("/subjects", response_model=list[SubjectSummaryRead])
async def read_subjects(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await list_subjects(db, user.id)


@router.get("/subjects/{subject_id}", response_model=SubjectDetailRead)
async def read_subject_detail(
    subject_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await get_subject_detail(db, user.id, subject_id)


@router.get("/subjects/{subject_id}/modules", response_model=list[ModuleDetailRead])
async def read_subject_modules(
    subject_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await get_subject_modules(db, subject_id)


@router.get("/lessons/{lesson_id}", response_model=LessonDetailRead)
async def read_lesson_detail(
    lesson_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await get_lesson_detail(db, lesson_id)
