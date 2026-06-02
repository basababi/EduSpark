from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User
from app.schemas import (
    QuizAttemptHistoryItemRead,
    QuizAttemptSubmitRequest,
    QuizAttemptSubmitResponse,
    QuizDetailRead,
    QuizListItemRead,
)
from app.services.quiz_service import (
    get_quiz_attempt_history,
    get_quiz_detail,
    list_quizzes,
    submit_quiz_attempt,
)

router = APIRouter(prefix="/quizzes", tags=["quizzes"])


@router.get("", response_model=list[QuizListItemRead])
async def read_quizzes(
    subject_id: UUID | None = Query(default=None),
    topic_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await list_quizzes(
        db,
        user,
        subject_id=subject_id,
        topic_id=topic_id,
    )


@router.get("/attempts/history", response_model=list[QuizAttemptHistoryItemRead])
async def read_quiz_attempt_history(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await get_quiz_attempt_history(db, user, limit=limit)


@router.get("/{quiz_id}", response_model=QuizDetailRead)
async def read_quiz_detail(
    quiz_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await get_quiz_detail(db, quiz_id)


@router.post("/{quiz_id}/attempts", response_model=QuizAttemptSubmitResponse)
async def create_quiz_attempt(
    quiz_id: UUID,
    payload: QuizAttemptSubmitRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await submit_quiz_attempt(db, user, quiz_id, payload)
