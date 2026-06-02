"""add user preferences table

Revision ID: 20260404_0002
Revises: 20260318_0001
Create Date: 2026-04-04 12:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260404_0002"
down_revision: Union[str, None] = "20260318_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "userpreference",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("interests", sa.JSON(), nullable=False),
        sa.Column("email_notifications", sa.Boolean(), nullable=False),
        sa.Column("weekly_report", sa.Boolean(), nullable=False),
        sa.Column("daily_reminder", sa.Boolean(), nullable=False),
        sa.Column("dark_mode", sa.Boolean(), nullable=False),
        sa.Column("compact_view", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("user_id"),
    )
    op.execute(
        """
        INSERT INTO userpreference (
            user_id,
            interests,
            email_notifications,
            weekly_report,
            daily_reminder,
            dark_mode,
            compact_view,
            updated_at
        )
        SELECT
            u.id,
            '[]'::json,
            TRUE,
            FALSE,
            TRUE,
            FALSE,
            FALSE,
            NOW()
        FROM "user" u
        WHERE NOT EXISTS (
            SELECT 1
            FROM userpreference up
            WHERE up.user_id = u.id
        )
        """
    )


def downgrade() -> None:
    op.drop_table("userpreference")
