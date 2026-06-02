from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AuditLog,
    Module,
    ProgressSnapshot,
    Quiz,
    QuizAttempt,
    StudySession,
    Subject,
    Topic,
    User,
)
from app.schemas import (
    ProgressSnapshotRead,
    ProgressSummaryRead,
    StudySessionCreate,
    StudySessionRead,
    SubjectProgressRead,
    WeeklyTrendPointRead,
)

DEFAULT_WEEKLY_GOAL_MINUTES = 22 * 60
SUBJECT_STUDY_TARGET_MINUTES = 5 * 60


def _to_float(value: float | None) -> float:
    if value is None:
        return 0.0
    return float(value)


def _build_subject_progress(
    *,
    subject_id: UUID,
    subject_name: str,
    average_quiz_score: float | None,
    study_minutes: int,
    completed_quizzes: int,
) -> SubjectProgressRead:
    study_percent = min((study_minutes / SUBJECT_STUDY_TARGET_MINUTES) * 100, 100.0)
    if average_quiz_score is None:
        progress_percent = round(study_percent, 2)
    else:
        progress_percent = round((average_quiz_score * 0.75) + (study_percent * 0.25), 2)

    return SubjectProgressRead(
        subject_id=subject_id,
        subject_name=subject_name,
        progress_percent=progress_percent,
        average_quiz_score=round(average_quiz_score, 2) if average_quiz_score is not None else None,
        study_minutes=study_minutes,
        completed_quizzes=completed_quizzes,
    )


async def record_study_session(
    db: AsyncSession,
    user: User,
    payload: StudySessionCreate,
) -> StudySessionRead:
    studied_at = payload.studied_at or datetime.now(timezone.utc)
    session = StudySession(
        user_id=user.id,
        subject_id=payload.subject_id,
        duration_minutes=payload.duration_minutes,
        studied_at=studied_at,
    )
    db.add(session)
    await db.flush()

    db.add(
        ProgressSnapshot(
            user_id=user.id,
            subject_id=payload.subject_id,
            metric={
                "event": "study_session_recorded",
                "duration_minutes": payload.duration_minutes,
                "studied_at": studied_at.isoformat(),
            },
        )
    )
    db.add(
        AuditLog(
            user_id=user.id,
            action="study_session_recorded",
            entity="studysession",
            entity_id=str(session.id),
        )
    )
    await db.commit()
    await db.refresh(session)
    return StudySessionRead.model_validate(session)


async def get_progress_summary(
    db: AsyncSession,
    user: User,
    *,
    days: int = 7,
    weekly_goal_minutes: int = DEFAULT_WEEKLY_GOAL_MINUTES,
) -> ProgressSummaryRead:
    safe_days = max(1, min(days, 30))
    window_start = datetime.now(timezone.utc) - timedelta(days=safe_days - 1)

    weekly_minutes_stmt = select(func.coalesce(func.sum(StudySession.duration_minutes), 0)).where(
        StudySession.user_id == user.id,
        StudySession.studied_at >= window_start,
    )
    weekly_minutes = int((await db.execute(weekly_minutes_stmt)).scalar_one())

    trend_stmt = (
        select(
            func.date(StudySession.studied_at).label("day"),
            func.coalesce(func.sum(StudySession.duration_minutes), 0).label("minutes"),
        )
        .where(
            StudySession.user_id == user.id,
            StudySession.studied_at >= window_start,
        )
        .group_by(func.date(StudySession.studied_at))
    )
    trend_rows = (await db.execute(trend_stmt)).all()
    trend_map: dict[date, int] = {
        row.day: int(row.minutes or 0) for row in trend_rows if row.day is not None
    }
    weekly_trend = [
        WeeklyTrendPointRead(
            date=(window_start.date() + timedelta(days=offset)),
            minutes=trend_map.get(window_start.date() + timedelta(days=offset), 0),
        )
        for offset in range(safe_days)
    ]

    quiz_summary_stmt = select(
        func.avg(QuizAttempt.score).label("average_score"),
        func.count(QuizAttempt.id).label("completed_quizzes"),
    ).where(
        QuizAttempt.user_id == user.id,
        QuizAttempt.completed_at.is_not(None),
    )
    quiz_summary = (await db.execute(quiz_summary_stmt)).one()
    average_quiz_score = round(_to_float(quiz_summary.average_score), 2)
    completed_quizzes = int(quiz_summary.completed_quizzes or 0)

    study_by_subject_stmt = (
        select(
            StudySession.subject_id,
            func.coalesce(func.sum(StudySession.duration_minutes), 0).label("study_minutes"),
        )
        .where(
            StudySession.user_id == user.id,
            StudySession.subject_id.is_not(None),
        )
        .group_by(StudySession.subject_id)
    )
    study_by_subject_rows = (await db.execute(study_by_subject_stmt)).all()
    study_by_subject = {
        row.subject_id: int(row.study_minutes or 0)
        for row in study_by_subject_rows
        if row.subject_id is not None
    }

    quiz_by_subject_stmt = (
        select(
            Module.subject_id.label("subject_id"),
            func.avg(QuizAttempt.score).label("average_score"),
            func.count(QuizAttempt.id).label("completed_quizzes"),
        )
        .select_from(QuizAttempt)
        .join(Quiz, Quiz.id == QuizAttempt.quiz_id)
        .join(Topic, Topic.id == Quiz.topic_id)
        .join(Module, Module.id == Topic.module_id)
        .where(
            QuizAttempt.user_id == user.id,
            QuizAttempt.completed_at.is_not(None),
        )
        .group_by(Module.subject_id)
    )
    quiz_by_subject_rows = (await db.execute(quiz_by_subject_stmt)).all()
    quiz_by_subject = {
        row.subject_id: (
            round(_to_float(row.average_score), 2) if row.average_score is not None else None,
            int(row.completed_quizzes or 0),
        )
        for row in quiz_by_subject_rows
        if row.subject_id is not None
    }

    subject_rows = (
        await db.execute(select(Subject.id, Subject.name).order_by(Subject.name.asc()))
    ).all()
    subject_progress = [
        _build_subject_progress(
            subject_id=row.id,
            subject_name=row.name,
            average_quiz_score=quiz_by_subject.get(row.id, (None, 0))[0],
            study_minutes=study_by_subject.get(row.id, 0),
            completed_quizzes=quiz_by_subject.get(row.id, (None, 0))[1],
        )
        for row in subject_rows
    ]
    subject_progress.sort(
        key=lambda item: (-item.progress_percent, item.subject_name.casefold())
    )

    weekly_goal_percent = round(min((weekly_minutes / weekly_goal_minutes) * 100, 100.0), 2)
    weekly_hours = round(weekly_minutes / 60, 2)
    completed_lessons = completed_quizzes

    return ProgressSummaryRead(
        weekly_minutes=weekly_minutes,
        weekly_hours=weekly_hours,
        weekly_goal_minutes=weekly_goal_minutes,
        weekly_goal_percent=weekly_goal_percent,
        average_quiz_score=average_quiz_score,
        completed_quizzes=completed_quizzes,
        completed_lessons=completed_lessons,
        subject_progress=subject_progress,
        weekly_trend=weekly_trend,
    )


async def get_progress_snapshots(
    db: AsyncSession,
    user: User,
    *,
    limit: int = 20,
) -> list[ProgressSnapshotRead]:
    safe_limit = max(1, min(limit, 100))
    snapshots = (
        await db.execute(
            select(ProgressSnapshot)
            .where(ProgressSnapshot.user_id == user.id)
            .order_by(ProgressSnapshot.captured_at.desc())
            .limit(safe_limit)
        )
    ).scalars()
    return [ProgressSnapshotRead.model_validate(item) for item in snapshots]
