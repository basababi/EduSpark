import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Document(Base):
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    uploaded_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("user.id"))
    source_name: Mapped[str] = mapped_column(String(255))
    source_type: Mapped[str | None] = mapped_column(String(50))
    subject: Mapped[str | None] = mapped_column(String(80))
    topic: Mapped[str | None] = mapped_column(String(120))
    grade_level: Mapped[str | None] = mapped_column(String(30))
    difficulty: Mapped[str | None] = mapped_column(String(20))
    language: Mapped[str | None] = mapped_column(String(10))
    status: Mapped[str | None] = mapped_column(String(20), default="pending")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class DocumentChunk(Base):
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("document.id"))
    chunk_index: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    # Use plain float array for embedding to avoid missing pgvector driver in base image
    embedding: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Column is named "metadata" in the DB, but the attribute name must avoid SQLAlchemy's reserved "metadata"
    chunk_metadata: Mapped[str | None] = mapped_column("metadata", Text)


class EmbeddingMetadata(Base):
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("document.id"))
    chunk_id: Mapped[str] = mapped_column(String(36), ForeignKey("documentchunk.id"))
    provider: Mapped[str | None] = mapped_column(String(50))
    vector_size: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class RetrievalLog(Base):
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("user.id"))
    query: Mapped[str] = mapped_column(Text)
    source_used: Mapped[str | None] = mapped_column(String(30))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    score: Mapped[float | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)




