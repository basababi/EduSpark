from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LessonSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    summary: str | None = None


class TopicDetailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    objective: str | None = None
    difficulty: str | None = None
    lessons: list[LessonSummaryRead] = Field(default_factory=list)


class ModuleDetailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None = None
    order: int | None = None
    topics: list[TopicDetailRead] = Field(default_factory=list)


class SubjectSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    difficulty_level: str | None = None
    modules_count: int
    topics_count: int
    lessons_count: int
    progress_percent: float = 0.0


class SubjectDetailRead(SubjectSummaryRead):
    modules: list[ModuleDetailRead] = Field(default_factory=list)


class LessonContentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    content_type: str
    text_content: str
    source: str | None = None
    language: str | None = None


class LessonDetailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    summary: str | None = None
    subject_id: UUID | None = None
    subject_name: str | None = None
    module_id: UUID | None = None
    module_title: str | None = None
    topic_id: UUID
    topic_title: str
    contents: list[LessonContentRead] = Field(default_factory=list)
