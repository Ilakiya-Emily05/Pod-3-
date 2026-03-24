"""add cefr grading fields

Revision ID: a91b2c3d4e5f
Revises: 620aa2067f08
Create Date: 2026-03-24 16:35:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a91b2c3d4e5f"
down_revision: str | Sequence[str] | None = "620aa2067f08"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    cefr_level_enum = postgresql.ENUM(
        "A1",
        "A2",
        "B1",
        "B2",
        "C1",
        "C2",
        name="cefr_level_enum",
    )
    cefr_level_enum.create(op.get_bind(), checkfirst=True)

    # Question-level CEFR source metadata
    op.add_column(
        "reading_questions",
        sa.Column(
            "cefr_level",
            postgresql.ENUM(
                "A1",
                "A2",
                "B1",
                "B2",
                "C1",
                "C2",
                name="cefr_level_enum",
                create_type=False,
            ),
            nullable=True,
        ),
    )
    op.add_column(
        "reading_questions",
        sa.Column("difficulty_score", sa.Numeric(precision=6, scale=2), nullable=True),
    )
    op.add_column(
        "grammar_questions",
        sa.Column(
            "cefr_level",
            postgresql.ENUM(
                "A1",
                "A2",
                "B1",
                "B2",
                "C1",
                "C2",
                name="cefr_level_enum",
                create_type=False,
            ),
            nullable=True,
        ),
    )
    op.add_column(
        "grammar_questions",
        sa.Column("difficulty_score", sa.Numeric(precision=6, scale=2), nullable=True),
    )
    op.add_column(
        "listening_questions",
        sa.Column(
            "cefr_level",
            postgresql.ENUM(
                "A1",
                "A2",
                "B1",
                "B2",
                "C1",
                "C2",
                name="cefr_level_enum",
                create_type=False,
            ),
            nullable=True,
        ),
    )
    op.add_column(
        "listening_questions",
        sa.Column("difficulty_score", sa.Numeric(precision=6, scale=2), nullable=True),
    )

    # Attempt-answer CEFR snapshot metadata
    op.add_column(
        "reading_attempt_answers",
        sa.Column(
            "cefr_level",
            postgresql.ENUM(
                "A1",
                "A2",
                "B1",
                "B2",
                "C1",
                "C2",
                name="cefr_level_enum",
                create_type=False,
            ),
            nullable=True,
        ),
    )
    op.add_column(
        "reading_attempt_answers",
        sa.Column("difficulty_score", sa.Numeric(precision=6, scale=2), nullable=True),
    )
    op.add_column(
        "grammar_attempt_answers",
        sa.Column(
            "cefr_level",
            postgresql.ENUM(
                "A1",
                "A2",
                "B1",
                "B2",
                "C1",
                "C2",
                name="cefr_level_enum",
                create_type=False,
            ),
            nullable=True,
        ),
    )
    op.add_column(
        "grammar_attempt_answers",
        sa.Column("difficulty_score", sa.Numeric(precision=6, scale=2), nullable=True),
    )
    op.add_column(
        "listening_attempt_answers",
        sa.Column(
            "cefr_level",
            postgresql.ENUM(
                "A1",
                "A2",
                "B1",
                "B2",
                "C1",
                "C2",
                name="cefr_level_enum",
                create_type=False,
            ),
            nullable=True,
        ),
    )
    op.add_column(
        "listening_attempt_answers",
        sa.Column("difficulty_score", sa.Numeric(precision=6, scale=2), nullable=True),
    )

    # Attempt-level result fields replacing score
    op.add_column(
        "reading_attempts",
        sa.Column("ability_score", sa.Numeric(precision=6, scale=4), nullable=True),
    )
    op.add_column(
        "reading_attempts",
        sa.Column("cefr_level", sa.String(length=3), nullable=True),
    )
    op.drop_column("reading_attempts", "score")

    op.add_column(
        "grammar_attempts",
        sa.Column("ability_score", sa.Numeric(precision=6, scale=4), nullable=True),
    )
    op.add_column(
        "grammar_attempts",
        sa.Column("cefr_level", sa.String(length=3), nullable=True),
    )
    op.drop_column("grammar_attempts", "score")

    op.add_column(
        "listening_attempts",
        sa.Column("ability_score", sa.Numeric(precision=6, scale=4), nullable=True),
    )
    op.add_column(
        "listening_attempts",
        sa.Column("cefr_level", sa.String(length=3), nullable=True),
    )
    op.drop_column("listening_attempts", "score")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "listening_attempts",
        sa.Column(
            "score",
            sa.Numeric(precision=6, scale=2),
            nullable=False,
            server_default=sa.text("0.00"),
        ),
    )
    op.drop_column("listening_attempts", "cefr_level")
    op.drop_column("listening_attempts", "ability_score")

    op.add_column(
        "grammar_attempts",
        sa.Column(
            "score",
            sa.Numeric(precision=6, scale=2),
            nullable=False,
            server_default=sa.text("0.00"),
        ),
    )
    op.drop_column("grammar_attempts", "cefr_level")
    op.drop_column("grammar_attempts", "ability_score")

    op.add_column(
        "reading_attempts",
        sa.Column(
            "score",
            sa.Numeric(precision=6, scale=2),
            nullable=False,
            server_default=sa.text("0.00"),
        ),
    )
    op.drop_column("reading_attempts", "cefr_level")
    op.drop_column("reading_attempts", "ability_score")

    op.drop_column("listening_attempt_answers", "difficulty_score")
    op.drop_column("listening_attempt_answers", "cefr_level")
    op.drop_column("grammar_attempt_answers", "difficulty_score")
    op.drop_column("grammar_attempt_answers", "cefr_level")
    op.drop_column("reading_attempt_answers", "difficulty_score")
    op.drop_column("reading_attempt_answers", "cefr_level")

    op.drop_column("listening_questions", "difficulty_score")
    op.drop_column("listening_questions", "cefr_level")
    op.drop_column("grammar_questions", "difficulty_score")
    op.drop_column("grammar_questions", "cefr_level")
    op.drop_column("reading_questions", "difficulty_score")
    op.drop_column("reading_questions", "cefr_level")

    cefr_level_enum = postgresql.ENUM(
        "A1",
        "A2",
        "B1",
        "B2",
        "C1",
        "C2",
        name="cefr_level_enum",
    )
    cefr_level_enum.drop(op.get_bind(), checkfirst=True)
