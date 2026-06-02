from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Lesson, Module, Quiz, QuizAttempt, Subject, Topic
from app.schemas import (
    LessonContentRead,
    LessonDetailRead,
    LessonSummaryRead,
    ModuleDetailRead,
    SubjectDetailRead,
    SubjectSummaryRead,
    TopicDetailRead,
)


def _round_score(value: float | None) -> float:
    if value is None:
        return 0.0
    return round(float(value), 2)


async def _subject_progress_map(db: AsyncSession, user_id: UUID) -> dict[UUID, float]:
    stmt = (
        select(
            Module.subject_id.label("subject_id"),
            func.avg(QuizAttempt.score).label("average_score"),
        )
        .select_from(QuizAttempt)
        .join(Quiz, Quiz.id == QuizAttempt.quiz_id)
        .join(Topic, Topic.id == Quiz.topic_id)
        .join(Module, Module.id == Topic.module_id)
        .where(
            QuizAttempt.user_id == user_id,
            QuizAttempt.completed_at.is_not(None),
        )
        .group_by(Module.subject_id)
    )
    rows = (await db.execute(stmt)).all()
    return {row.subject_id: _round_score(row.average_score) for row in rows if row.subject_id}


def _build_module_detail(module: Module) -> ModuleDetailRead:
    sorted_topics = sorted(
        module.topics,
        key=lambda item: (item.title.casefold(), item.created_at),
    )
    topics = [
        TopicDetailRead(
            id=topic.id,
            title=topic.title,
            objective=topic.objective,
            difficulty=topic.difficulty,
            lessons=[
                LessonSummaryRead(
                    id=lesson.id,
                    title=lesson.title,
                    summary=lesson.summary,
                )
                for lesson in sorted(
                    topic.lessons,
                    key=lambda lesson_item: (lesson_item.title.casefold(), lesson_item.created_at),
                )
            ],
        )
        for topic in sorted_topics
    ]
    return ModuleDetailRead(
        id=module.id,
        title=module.title,
        description=module.description,
        order=module.order,
        topics=topics,
    )


def _count_structure(modules: list[Module]) -> tuple[int, int, int]:
    module_count = len(modules)
    topic_count = sum(len(module.topics) for module in modules)
    lesson_count = sum(len(topic.lessons) for module in modules for topic in module.topics)
    return module_count, topic_count, lesson_count


async def list_subjects(db: AsyncSession, user_id: UUID) -> list[SubjectSummaryRead]:
    stmt = (
        select(
            Subject.id,
            Subject.name,
            Subject.description,
            Subject.difficulty_level,
            func.count(func.distinct(Module.id)).label("modules_count"),
            func.count(func.distinct(Topic.id)).label("topics_count"),
            func.count(func.distinct(Lesson.id)).label("lessons_count"),
        )
        .outerjoin(Module, Module.subject_id == Subject.id)
        .outerjoin(Topic, Topic.module_id == Module.id)
        .outerjoin(Lesson, Lesson.topic_id == Topic.id)
        .group_by(Subject.id)
        .order_by(Subject.name.asc())
    )
    rows = (await db.execute(stmt)).all()
    progress_map = await _subject_progress_map(db, user_id)
    return [
        SubjectSummaryRead(
            id=row.id,
            name=row.name,
            description=row.description,
            difficulty_level=row.difficulty_level,
            modules_count=int(row.modules_count or 0),
            topics_count=int(row.topics_count or 0),
            lessons_count=int(row.lessons_count or 0),
            progress_percent=progress_map.get(row.id, 0.0),
        )
        for row in rows
    ]


async def get_subject_detail(db: AsyncSession, user_id: UUID, subject_id: UUID) -> SubjectDetailRead:
    stmt = (
        select(Subject)
        .options(
            selectinload(Subject.modules)
            .selectinload(Module.topics)
            .selectinload(Topic.lessons)
        )
        .where(Subject.id == subject_id)
    )
    subject = (await db.execute(stmt)).scalar_one_or_none()
    if subject is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")

    sorted_modules = sorted(
        subject.modules,
        key=lambda item: (item.order is None, item.order or 0, item.title.casefold()),
    )
    module_count, topic_count, lesson_count = _count_structure(sorted_modules)
    progress_map = await _subject_progress_map(db, user_id)

    return SubjectDetailRead(
        id=subject.id,
        name=subject.name,
        description=subject.description,
        difficulty_level=subject.difficulty_level,
        modules_count=module_count,
        topics_count=topic_count,
        lessons_count=lesson_count,
        progress_percent=progress_map.get(subject.id, 0.0),
        modules=[_build_module_detail(module) for module in sorted_modules],
    )


async def get_subject_modules(db: AsyncSession, subject_id: UUID) -> list[ModuleDetailRead]:
    stmt = (
        select(Subject)
        .options(
            selectinload(Subject.modules)
            .selectinload(Module.topics)
            .selectinload(Topic.lessons)
        )
        .where(Subject.id == subject_id)
    )
    subject = (await db.execute(stmt)).scalar_one_or_none()
    if subject is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")

    sorted_modules = sorted(
        subject.modules,
        key=lambda item: (item.order is None, item.order or 0, item.title.casefold()),
    )
    return [_build_module_detail(module) for module in sorted_modules]


async def get_lesson_detail(db: AsyncSession, lesson_id: UUID) -> LessonDetailRead:
    stmt = (
        select(
            Lesson,
            Topic.id.label("topic_id"),
            Topic.title.label("topic_title"),
            Module.id.label("module_id"),
            Module.title.label("module_title"),
            Subject.id.label("subject_id"),
            Subject.name.label("subject_name"),
        )
        .join(Topic, Topic.id == Lesson.topic_id)
        .join(Module, Module.id == Topic.module_id)
        .join(Subject, Subject.id == Module.subject_id)
        .options(selectinload(Lesson.contents))
        .where(Lesson.id == lesson_id)
    )
    row = (await db.execute(stmt)).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    lesson = row.Lesson
    sorted_contents = sorted(
        lesson.contents,
        key=lambda item: (item.created_at, item.id),
    )
    return LessonDetailRead(
        id=lesson.id,
        title=lesson.title,
        summary=lesson.summary,
        subject_id=row.subject_id,
        subject_name=row.subject_name,
        module_id=row.module_id,
        module_title=row.module_title,
        topic_id=row.topic_id,
        topic_title=row.topic_title,
        contents=[
            LessonContentRead(
                id=content.id,
                content_type=content.content_type,
                text_content=content.text_content,
                source=content.source,
                language=content.language,
            )
            for content in sorted_contents
        ],
    )
