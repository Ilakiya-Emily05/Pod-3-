"""extend mock interview schema

Revision ID: f7ce66971a52
Revises: b1a2c3d4e5f6
Create Date: 2026-04-21 12:40:06.346703

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "f7ce66971a52"
down_revision: Union[str, Sequence[str], None] = "b1a2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "interview_sessions",
        sa.Column("cefr_level", sa.String(length=10), nullable=True),
    )
    op.add_column(
        "interview_sessions",
        sa.Column(
            "domain",
            sa.String(length=50),
            server_default="general",
            nullable=False,
        ),
    )
    op.add_column(
        "interview_sessions",
        sa.Column(
            "total_questions",
            sa.Integer(),
            server_default="8",
            nullable=False,
        ),
    )
    op.add_column(
        "interview_sessions",
        sa.Column(
            "questions_answered",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )
    op.add_column(
        "interview_sessions",
        sa.Column(
            "total_score",
            sa.Numeric(precision=5, scale=2),
            nullable=True,
        ),
    )
    op.add_column(
        "interview_sessions",
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )

    op.add_column(
        "user_responses",
        sa.Column("question_order", sa.Integer(), nullable=True),
    )
    op.add_column(
        "user_responses",
        sa.Column("audio_url", sa.Text(), nullable=True),
    )
    op.add_column(
        "user_responses",
        sa.Column(
            "score",
            sa.Numeric(precision=5, scale=2),
            nullable=True,
        ),
    )
    op.add_column(
        "user_responses",
        sa.Column(
            "score_breakdown",
            sa.JSON(),
            server_default="{}",
            nullable=True,
        ),
    )
    op.add_column(
        "user_responses",
        sa.Column(
            "answered_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("user_responses", "answered_at")
    op.drop_column("user_responses", "score_breakdown")
    op.drop_column("user_responses", "score")
    op.drop_column("user_responses", "audio_url")
    op.drop_column("user_responses", "question_order")

    op.drop_column("interview_sessions", "completed_at")
    op.drop_column("interview_sessions", "total_score")
    op.drop_column("interview_sessions", "questions_answered")
    op.drop_column("interview_sessions", "total_questions")
    op.drop_column("interview_sessions", "domain")
    op.drop_column("interview_sessions", "cefr_level")