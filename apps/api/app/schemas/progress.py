from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StudySessionCreate(BaseModel):
    subject_id: UUID | None = None
    duration_minutes: int = Field(gt=0, le=720)
    studied_at: datetime | None = None


class StudySessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subject_id: UUID | None = None
    duration_minutes: int
    studied_at: datetime


class WeeklyTrendPointRead(BaseModel):
    date: date
    minutes: int


class SubjectProgressRead(BaseModel):
    subject_id: UUID
    subject_name: str
    progress_percent: float
    average_quiz_score: float | None = None
    study_minutes: int
    completed_quizzes: int


class ProgressSummaryRead(BaseModel):
    weekly_minutes: int
    weekly_hours: float
    weekly_goal_minutes: int
    weekly_goal_percent: float
    average_quiz_score: float
    completed_quizzes: int
    completed_lessons: int
    subject_progress: list[SubjectProgressRead]
    weekly_trend: list[WeeklyTrendPointRead]


class ProgressSnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subject_id: UUID | None = None
    metric: dict
    captured_at: datetime
