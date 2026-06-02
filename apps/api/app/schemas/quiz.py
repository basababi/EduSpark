from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class QuizListItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    mode: str | None = None
    level: str | None = None
    topic_id: UUID | None = None
    topic_title: str | None = None
    subject_id: UUID | None = None
    subject_name: str | None = None
    question_count: int
    last_score: float | None = None
    last_attempt_at: datetime | None = None


class QuizQuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    question_text: str
    choices: dict[str, str]
    explanation: str | None = None


class QuizDetailRead(QuizListItemRead):
    questions: list[QuizQuestionRead] = Field(default_factory=list)


class QuizAnswerSubmit(BaseModel):
    question_id: UUID
    selected_answer: str = Field(min_length=1, max_length=10)


class QuizAttemptSubmitRequest(BaseModel):
    answers: list[QuizAnswerSubmit] = Field(min_length=1)


class QuizAttemptAnswerResultRead(BaseModel):
    question_id: UUID
    selected_answer: str | None = None
    correct_answer: str
    is_correct: bool
    explanation: str | None = None


class QuizAttemptSubmitResponse(BaseModel):
    attempt_id: UUID
    quiz_id: UUID
    score: float
    correct_count: int
    total_questions: int
    completed_at: datetime
    answers: list[QuizAttemptAnswerResultRead]


class QuizAttemptHistoryItemRead(BaseModel):
    attempt_id: UUID
    quiz_id: UUID
    quiz_title: str
    subject_name: str | None = None
    score: float | None = None
    correct_count: int
    total_questions: int
    completed_at: datetime | None = None
