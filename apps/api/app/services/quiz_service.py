from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AuditLog,
    Module,
    ProgressSnapshot,
    Quiz,
    QuizAnswer,
    QuizAttempt,
    QuizQuestion,
    Subject,
    Topic,
    User,
)
from app.schemas import (
    QuizAttemptAnswerResultRead,
    QuizAttemptHistoryItemRead,
    QuizAttemptSubmitRequest,
    QuizAttemptSubmitResponse,
    QuizDetailRead,
    QuizListItemRead,
    QuizQuestionRead,
)


def _round_score(value: float | None) -> float:
    if value is None:
        return 0.0
    return round(float(value), 2)


def _evaluate_answers(
    questions: list[QuizQuestion],
    payload: QuizAttemptSubmitRequest,
) -> tuple[float, int, list[QuizAttemptAnswerResultRead]]:
    if not questions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quiz has no questions",
        )

    submitted_answers: dict[UUID, str] = {}
    for item in payload.answers:
        if item.question_id in submitted_answers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate answers for the same question are not allowed",
            )
        submitted_answers[item.question_id] = item.selected_answer.strip()

    question_map = {question.id: question for question in questions}
    unknown_question_ids = [qid for qid in submitted_answers if qid not in question_map]
    if unknown_question_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Submitted answers contain unknown question ids",
        )

    results: list[QuizAttemptAnswerResultRead] = []
    correct_count = 0
    for question in sorted(questions, key=lambda item: item.question_text.casefold()):
        selected_answer = submitted_answers.get(question.id)
        is_correct = selected_answer is not None and selected_answer == question.correct_answer
        if is_correct:
            correct_count += 1
        results.append(
            QuizAttemptAnswerResultRead(
                question_id=question.id,
                selected_answer=selected_answer,
                correct_answer=question.correct_answer,
                is_correct=is_correct,
                explanation=question.explanation,
            )
        )

    total_questions = len(questions)
    score = round((correct_count / total_questions) * 100, 2)
    return score, correct_count, results


async def list_quizzes(
    db: AsyncSession,
    user: User,
    *,
    subject_id: UUID | None = None,
    topic_id: UUID | None = None,
) -> list[QuizListItemRead]:
    stmt = (
        select(
            Quiz.id,
            Quiz.title,
            Quiz.mode,
            Quiz.level,
            Quiz.topic_id,
            Topic.title.label("topic_title"),
            Subject.id.label("subject_id"),
            Subject.name.label("subject_name"),
            func.count(QuizQuestion.id).label("question_count"),
        )
        .select_from(Quiz)
        .outerjoin(Topic, Topic.id == Quiz.topic_id)
        .outerjoin(Module, Module.id == Topic.module_id)
        .outerjoin(Subject, Subject.id == Module.subject_id)
        .outerjoin(QuizQuestion, QuizQuestion.quiz_id == Quiz.id)
        .group_by(Quiz.id, Topic.id, Subject.id)
        .order_by(Quiz.created_at.desc(), Quiz.title.asc())
    )
    if subject_id:
        stmt = stmt.where(Subject.id == subject_id)
    if topic_id:
        stmt = stmt.where(Quiz.topic_id == topic_id)

    quiz_rows = (await db.execute(stmt)).all()

    attempts_stmt = (
        select(QuizAttempt.quiz_id, QuizAttempt.score, QuizAttempt.completed_at)
        .where(
            QuizAttempt.user_id == user.id,
            QuizAttempt.completed_at.is_not(None),
        )
        .order_by(QuizAttempt.completed_at.desc())
    )
    latest_attempt_by_quiz: dict[UUID, tuple[float | None, datetime | None]] = {}
    for row in (await db.execute(attempts_stmt)).all():
        if row.quiz_id not in latest_attempt_by_quiz:
            latest_attempt_by_quiz[row.quiz_id] = (row.score, row.completed_at)

    quizzes: list[QuizListItemRead] = []
    for row in quiz_rows:
        latest_attempt = latest_attempt_by_quiz.get(row.id)
        last_score = _round_score(latest_attempt[0]) if latest_attempt else None
        last_attempt_at = latest_attempt[1] if latest_attempt else None
        quizzes.append(
            QuizListItemRead(
                id=row.id,
                title=row.title,
                mode=row.mode,
                level=row.level,
                topic_id=row.topic_id,
                topic_title=row.topic_title,
                subject_id=row.subject_id,
                subject_name=row.subject_name,
                question_count=int(row.question_count or 0),
                last_score=last_score,
                last_attempt_at=last_attempt_at,
            )
        )
    return quizzes


async def get_quiz_detail(db: AsyncSession, quiz_id: UUID) -> QuizDetailRead:
    quiz_stmt = (
        select(
            Quiz.id,
            Quiz.title,
            Quiz.mode,
            Quiz.level,
            Quiz.topic_id,
            Topic.title.label("topic_title"),
            Subject.id.label("subject_id"),
            Subject.name.label("subject_name"),
        )
        .select_from(Quiz)
        .outerjoin(Topic, Topic.id == Quiz.topic_id)
        .outerjoin(Module, Module.id == Topic.module_id)
        .outerjoin(Subject, Subject.id == Module.subject_id)
        .where(Quiz.id == quiz_id)
    )
    quiz_row = (await db.execute(quiz_stmt)).first()
    if quiz_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")

    question_rows = (
        await db.execute(
            select(QuizQuestion)
            .where(QuizQuestion.quiz_id == quiz_id)
            .order_by(QuizQuestion.question_text.asc())
        )
    ).scalars()
    questions = list(question_rows)

    return QuizDetailRead(
        id=quiz_row.id,
        title=quiz_row.title,
        mode=quiz_row.mode,
        level=quiz_row.level,
        topic_id=quiz_row.topic_id,
        topic_title=quiz_row.topic_title,
        subject_id=quiz_row.subject_id,
        subject_name=quiz_row.subject_name,
        question_count=len(questions),
        questions=[
            QuizQuestionRead(
                id=question.id,
                question_text=question.question_text,
                choices=question.choices,
                explanation=question.explanation,
            )
            for question in questions
        ],
        last_score=None,
        last_attempt_at=None,
    )


async def submit_quiz_attempt(
    db: AsyncSession,
    user: User,
    quiz_id: UUID,
    payload: QuizAttemptSubmitRequest,
) -> QuizAttemptSubmitResponse:
    quiz_stmt = (
        select(
            Quiz.id,
            Module.subject_id.label("subject_id"),
        )
        .select_from(Quiz)
        .outerjoin(Topic, Topic.id == Quiz.topic_id)
        .outerjoin(Module, Module.id == Topic.module_id)
        .where(Quiz.id == quiz_id)
    )
    quiz_row = (await db.execute(quiz_stmt)).first()
    if quiz_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")

    question_rows = (
        await db.execute(select(QuizQuestion).where(QuizQuestion.quiz_id == quiz_id))
    ).scalars()
    questions = list(question_rows)

    score, correct_count, answer_results = _evaluate_answers(questions, payload)
    completed_at = datetime.now(timezone.utc)

    attempt = QuizAttempt(
        quiz_id=quiz_id,
        user_id=user.id,
        score=score,
        completed_at=completed_at,
    )
    db.add(attempt)
    await db.flush()

    submitted_answer_map = {answer.question_id: answer.selected_answer.strip() for answer in payload.answers}
    for question in questions:
        selected = submitted_answer_map.get(question.id)
        if selected is None:
            continue
        db.add(
            QuizAnswer(
                attempt_id=attempt.id,
                question_id=question.id,
                selected_answer=selected,
                is_correct=selected == question.correct_answer,
                feedback=question.explanation,
            )
        )

    db.add(
        ProgressSnapshot(
            user_id=user.id,
            subject_id=quiz_row.subject_id,
            metric={
                "event": "quiz_attempt_submitted",
                "quiz_id": str(quiz_id),
                "attempt_id": str(attempt.id),
                "score": score,
                "correct_count": correct_count,
                "total_questions": len(questions),
            },
        )
    )
    db.add(
        AuditLog(
            user_id=user.id,
            action="quiz_attempt_submitted",
            entity="quiz",
            entity_id=str(quiz_id),
        )
    )
    await db.commit()

    return QuizAttemptSubmitResponse(
        attempt_id=attempt.id,
        quiz_id=quiz_id,
        score=score,
        correct_count=correct_count,
        total_questions=len(questions),
        completed_at=completed_at,
        answers=answer_results,
    )


async def get_quiz_attempt_history(
    db: AsyncSession,
    user: User,
    *,
    limit: int = 20,
) -> list[QuizAttemptHistoryItemRead]:
    safe_limit = max(1, min(limit, 100))
    attempts_stmt = (
        select(
            QuizAttempt.id.label("attempt_id"),
            QuizAttempt.quiz_id,
            QuizAttempt.score,
            QuizAttempt.completed_at,
            Quiz.title.label("quiz_title"),
            Subject.name.label("subject_name"),
        )
        .select_from(QuizAttempt)
        .join(Quiz, Quiz.id == QuizAttempt.quiz_id)
        .outerjoin(Topic, Topic.id == Quiz.topic_id)
        .outerjoin(Module, Module.id == Topic.module_id)
        .outerjoin(Subject, Subject.id == Module.subject_id)
        .where(
            QuizAttempt.user_id == user.id,
            QuizAttempt.completed_at.is_not(None),
        )
        .order_by(QuizAttempt.completed_at.desc())
        .limit(safe_limit)
    )
    attempt_rows = (await db.execute(attempts_stmt)).all()
    if not attempt_rows:
        return []

    attempt_ids = [row.attempt_id for row in attempt_rows]
    quiz_ids = list({row.quiz_id for row in attempt_rows})

    answer_counts_stmt = (
        select(
            QuizAnswer.attempt_id,
            func.coalesce(
                func.sum(case((QuizAnswer.is_correct.is_(True), 1), else_=0)),
                0,
            ).label("correct_count"),
        )
        .where(QuizAnswer.attempt_id.in_(attempt_ids))
        .group_by(QuizAnswer.attempt_id)
    )
    answer_count_rows = (await db.execute(answer_counts_stmt)).all()
    correct_count_map = {
        row.attempt_id: int(row.correct_count or 0)
        for row in answer_count_rows
    }

    total_questions_stmt = (
        select(
            QuizQuestion.quiz_id,
            func.count(QuizQuestion.id).label("total_questions"),
        )
        .where(QuizQuestion.quiz_id.in_(quiz_ids))
        .group_by(QuizQuestion.quiz_id)
    )
    total_question_rows = (await db.execute(total_questions_stmt)).all()
    total_question_map = {
        row.quiz_id: int(row.total_questions or 0)
        for row in total_question_rows
    }

    return [
        QuizAttemptHistoryItemRead(
            attempt_id=row.attempt_id,
            quiz_id=row.quiz_id,
            quiz_title=row.quiz_title,
            subject_name=row.subject_name,
            score=_round_score(row.score) if row.score is not None else None,
            correct_count=correct_count_map.get(row.attempt_id, 0),
            total_questions=total_question_map.get(row.quiz_id, 0),
            completed_at=row.completed_at,
        )
        for row in attempt_rows
    ]
