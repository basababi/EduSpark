"""init schema"""

from alembic import op
import sqlalchemy as sa
import uuid

revision = "20260318_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == 'postgresql'

    # PostgreSQL-д л vector extension
    if is_pg:
        op.execute('CREATE EXTENSION IF NOT EXISTS "vector";')

    op.create_table("role",
        sa.Column("id", sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
        sa.Column("description", sa.String(255)),
    )

    op.create_table("user",
        sa.Column("id", sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("role_id", sa.String(36), sa.ForeignKey("role.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_user_email", "user", ["email"], unique=True)

    op.create_table("profile",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("user.id"), primary_key=True),
        sa.Column("full_name", sa.String(120)),
        sa.Column("avatar_url", sa.String(255)),
        sa.Column("learner_level", sa.String(20), server_default="beginner"),
        sa.Column("locale", sa.String(10), server_default="mn"),
        sa.Column("timezone", sa.String(50), server_default="Asia/Ulaanbaatar"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table("subject",
        sa.Column("id", sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column("name", sa.String(120), unique=True, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("difficulty_level", sa.String(20)),
        sa.Column("created_by", sa.String(36)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table("module",
        sa.Column("id", sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column("subject_id", sa.String(36), sa.ForeignKey("subject.id")),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("order", sa.Integer),
    )

    op.create_table("topic",
        sa.Column("id", sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column("module_id", sa.String(36), sa.ForeignKey("module.id")),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("objective", sa.Text),
        sa.Column("difficulty", sa.String(20)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table("lesson",
        sa.Column("id", sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column("topic_id", sa.String(36), sa.ForeignKey("topic.id")),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("summary", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table("lessoncontent",
        sa.Column("id", sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column("lesson_id", sa.String(36), sa.ForeignKey("lesson.id")),
        sa.Column("content_type", sa.String(30), server_default="text"),
        sa.Column("text_content", sa.Text, nullable=False),
        sa.Column("source", sa.String(50)),
        sa.Column("language", sa.String(10), server_default="mn"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table("quiz",
        sa.Column("id", sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column("topic_id", sa.String(36), sa.ForeignKey("topic.id")),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("mode", sa.String(30)),
        sa.Column("level", sa.String(20)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table("quizquestion",
        sa.Column("id", sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column("quiz_id", sa.String(36), sa.ForeignKey("quiz.id")),
        sa.Column("question_text", sa.Text, nullable=False),
        sa.Column("choices", sa.Text, nullable=False),  # JSON string
        sa.Column("correct_answer", sa.String(10), nullable=False),
        sa.Column("explanation", sa.Text),
    )

    op.create_table("quizattempt",
        sa.Column("id", sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column("quiz_id", sa.String(36), sa.ForeignKey("quiz.id")),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("user.id")),
        sa.Column("score", sa.Float),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )

    op.create_table("quizanswer",
        sa.Column("id", sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column("attempt_id", sa.String(36), sa.ForeignKey("quizattempt.id")),
        sa.Column("question_id", sa.String(36), sa.ForeignKey("quizquestion.id")),
        sa.Column("selected_answer", sa.String(10), nullable=False),
        sa.Column("is_correct", sa.Boolean, server_default=sa.text("0")),
        sa.Column("feedback", sa.Text),
    )

    op.create_table("studysession",
        sa.Column("id", sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("user.id")),
        sa.Column("subject_id", sa.String(36), sa.ForeignKey("subject.id")),
        sa.Column("duration_minutes", sa.Integer, server_default="0"),
        sa.Column("studied_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table("progresssnapshot",
        sa.Column("id", sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("user.id")),
        sa.Column("subject_id", sa.String(36), sa.ForeignKey("subject.id")),
        sa.Column("metric", sa.Text, nullable=False),  # JSON string
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table("chatsession",
        sa.Column("id", sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("user.id")),
        sa.Column("subject_id", sa.String(36), sa.ForeignKey("subject.id")),
        sa.Column("mode", sa.String(20)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table("chatmessage",
        sa.Column("id", sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("chatsession.id")),
        sa.Column("role", sa.String(10), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("source_type", sa.String(30)),
        sa.Column("citations", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table("document",
        sa.Column("id", sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column("uploaded_by", sa.String(36), sa.ForeignKey("user.id")),
        sa.Column("source_name", sa.String(255), nullable=False),
        sa.Column("source_type", sa.String(50)),
        sa.Column("subject", sa.String(80)),
        sa.Column("topic", sa.String(120)),
        sa.Column("grade_level", sa.String(30)),
        sa.Column("difficulty", sa.String(20)),
        sa.Column("language", sa.String(10)),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table("documentchunk",
        sa.Column("id", sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("document.id")),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("embedding", sa.Text),  # JSON string
        sa.Column("metadata", sa.Text),   # JSON string
    )

    op.create_table("embeddingmetadata",
        sa.Column("id", sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("document.id")),
        sa.Column("chunk_id", sa.String(36), sa.ForeignKey("documentchunk.id")),
        sa.Column("provider", sa.String(50)),
        sa.Column("vector_size", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table("retrievallog",
        sa.Column("id", sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("user.id")),
        sa.Column("query", sa.Text, nullable=False),
        sa.Column("source_used", sa.String(30)),
        sa.Column("latency_ms", sa.Integer),
        sa.Column("score", sa.Float),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table("systemsetting",
        sa.Column("id", sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column("key", sa.String(120), nullable=False, unique=True),
        sa.Column("value", sa.Text),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table("auditlog",
        sa.Column("id", sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("user.id")),
        sa.Column("action", sa.String(120)),
        sa.Column("entity", sa.String(120)),
        sa.Column("entity_id", sa.String(120)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("auditlog")
    op.drop_table("systemsetting")
    op.drop_table("retrievallog")
    op.drop_table("embeddingmetadata")
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