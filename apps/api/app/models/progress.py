import uuid
from datetime import datetime

from sqlalchemy import Text, String, Date, DateTime, ForeignKey, Integer, JSON

from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StudySession(Base):
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("user.id"))
    subject_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("subject.id"))
    duration_minutes: Mapped[int] = mapped_column(Integer, default=0)
    studied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ProgressSnapshot(Base):
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("user.id"))
    subject_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("subject.id"))
    metric: Mapped[dict] = mapped_column(JSON)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)




