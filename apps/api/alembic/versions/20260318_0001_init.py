"""init schema"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = "20260318_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "vector";')

    op.create_table(
        "role",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("name", sa.String(length=50), nullable=False, unique=True),
        sa.Column("description", sa.String(length=255)),
    )

    op.create_table(
        "user",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("role.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_user_email", "user", ["email"], unique=True)

    op.create_table(
        "profile",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("user.id"), primary_key=True),
        sa.Column("full_name", sa.String(length=120)),
        sa.Column("avatar_url", sa.String(length=255)),
        sa.Column("learner_level", sa.String(length=20), server_default="beginner"),
        sa.Column("locale", sa.String(length=10), server_default="mn"),
        sa.Column("timezone", sa.String(length=50), server_default="Asia/Ulaanbaatar"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "subject",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("name", sa.String(length=120), unique=True, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("difficulty_level", sa.String(length=20)),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "module",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subject.id")),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("order", sa.Integer),
    )

    op.create_table(
        "topic",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("module_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("module.id")),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("objective", sa.Text),
        sa.Column("difficulty", sa.String(length=20)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "lesson",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topic.id")),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("summary", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "lessoncontent",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lesson.id")),
        sa.Column("content_type", sa.String(length=30), server_default="text"),
        sa.Column("text_content", sa.Text, nullable=False),
        sa.Column("source", sa.String(length=50)),
        sa.Column("language", sa.String(length=10), server_default="mn"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "quiz",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topic.id")),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("mode", sa.String(length=30)),
        sa.Column("level", sa.String(length=20)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "quizquestion",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("quiz_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quiz.id")),
        sa.Column("question_text", sa.Text, nullable=False),
        sa.Column("choices", postgresql.JSON, nullable=False),
        sa.Column("correct_answer", sa.String(length=10), nullable=False),
        sa.Column("explanation", sa.Text),
    )

    op.create_table(
        "quizattempt",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("quiz_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quiz.id")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("user.id")),
        sa.Column("score", sa.Float),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "quizanswer",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("attempt_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quizattempt.id")),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quizquestion.id")),
        sa.Column("selected_answer", sa.String(length=10), nullable=False),
        sa.Column("is_correct", sa.Boolean, server_default=sa.text("false")),
        sa.Column("feedback", sa.Text),
    )

    op.create_table(
        "studysession",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("user.id")),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subject.id")),
        sa.Column("duration_minutes", sa.Integer, server_default="0"),
        sa.Column("studied_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "progresssnapshot",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("user.id")),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subject.id")),
        sa.Column("metric", postgresql.JSON, nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "chatsession",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("user.id")),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subject.id")),
        sa.Column("mode", sa.String(length=20)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "chatmessage",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chatsession.id")),
        sa.Column("role", sa.String(length=10), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("source_type", sa.String(length=30)),
        sa.Column("citations", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "document",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("user.id")),
        sa.Column("source_name", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=50)),
        sa.Column("subject", sa.String(length=80)),
        sa.Column("topic", sa.String(length=120)),
        sa.Column("grade_level", sa.String(length=30)),
        sa.Column("difficulty", sa.String(length=20)),
        sa.Column("language", sa.String(length=10)),
        sa.Column("status", sa.String(length=20), server_default="pending"),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "documentchunk",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("document.id")),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("embedding", postgresql.ARRAY(sa.Float), nullable=True),
        sa.Column("metadata", postgresql.JSONB),
    )

    op.create_table(
        "embeddingmetadata",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("document.id")),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documentchunk.id")),
        sa.Column("provider", sa.String(length=50)),
        sa.Column("vector_size", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "retrievallog",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("user.id")),
        sa.Column("query", sa.Text, nullable=False),
        sa.Column("source_used", sa.String(length=30)),
        sa.Column("latency_ms", sa.Integer),
        sa.Column("score", sa.Float),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "systemsetting",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("key", sa.String(length=120), nullable=False, unique=True),
        sa.Column("value", sa.Text),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "auditlog",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("user.id")),
        sa.Column("action", sa.String(length=120)),
        sa.Column("entity", sa.String(length=120)),
        sa.Column("entity_id", sa.String(length=120)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("auditlog")
    op.drop_table("systemsetting")
    op.drop_table("retrievallog")
    op.drop_table("embeddingmetadata")
    op.drop_index("ix_documentchunk_embedding", table_name="documentchunk")
    op.drop_table("documentchunk")
    op.drop_table("document")
    op.drop_table("chatmessage")
    op.drop_table("chatsession")
    op.drop_table("progresssnapshot")
    op.drop_table("studysession")
    op.drop_table("quizanswer")
    op.drop_table("quizattempt")
    op.drop_table("quizquestion")
    op.drop_table("quiz")
    op.drop_table("lessoncontent")
    op.drop_table("lesson")
    op.drop_table("topic")
    op.drop_table("module")
    op.drop_table("subject")
    op.drop_table("profile")
    op.drop_index("ix_user_email", table_name="user")
    op.drop_table("user")
    op.drop_table("role")
