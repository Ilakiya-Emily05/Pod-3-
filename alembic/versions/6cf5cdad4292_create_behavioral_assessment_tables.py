"""create behavioral assessment tables

Revision ID: 6cf5cdad4292
Revises: b2f4c8d9e1a7
Create Date: 2026-03-29 19:39:43.543603

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6cf5cdad4292"
down_revision: str | Sequence[str] | None = "b2f4c8d9e1a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create behavioral tables with prefix
    op.create_table(
        "behav_questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("trait_type", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "behav_options",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("option_key", sa.String(), nullable=False),
        sa.Column("option_text", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["behav_questions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "behav_option_scores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("option_id", sa.Integer(), nullable=False),
        sa.Column("trait_name", sa.String(), nullable=False),
        sa.Column("score_value", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["option_id"],
            ["behav_options.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "behav_attempts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("overall_report", sa.JSON(), nullable=True),
        sa.Column("scores", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_behav_attempts_user_id"), "behav_attempts", ["user_id"], unique=False)
 
    op.create_table(
        "behav_user_answers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("attempt_id", sa.UUID(), nullable=True),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("option_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["attempt_id"],
            ["behav_attempts.id"],
        ),
        sa.ForeignKeyConstraint(
            ["option_id"],
            ["behav_options.id"],
        ),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["behav_questions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_behav_user_answers_user_id"), "behav_user_answers", ["user_id"], unique=False
    )

    # Generic table cleanup removed for safety as per code review.


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_behav_user_answers_user_id"), table_name="behav_user_answers")
    op.drop_table("behav_user_answers")
    op.drop_index(op.f("ix_behav_attempts_user_id"), table_name="behav_attempts")
    op.drop_table("behav_attempts")
    op.drop_table("behav_option_scores")
    op.drop_table("behav_options")
    op.drop_table("behav_questions")
