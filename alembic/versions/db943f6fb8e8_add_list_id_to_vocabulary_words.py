"""add list_id to vocabulary_words

Revision ID: db943f6fb8e8
Revises: 297ec505f124
Create Date: 2026-04-05 22:47:12.845833

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "db943f6fb8e8"
down_revision: str | Sequence[str] | None = "297ec505f124"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("vocabulary_words", sa.Column("list_id", sa.UUID(), nullable=True))
    op.create_index(
        op.f("ix_vocabulary_words_list_id"), "vocabulary_words", ["list_id"], unique=False
    )
    op.create_foreign_key(
        "fk_vocabulary_words_list_id_vocabulary_lists",
        "vocabulary_words",
        "vocabulary_lists",
        ["list_id"],
        ["list_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "fk_vocabulary_words_list_id_vocabulary_lists", "vocabulary_words", type_="foreignkey"
    )
    op.drop_index(op.f("ix_vocabulary_words_list_id"), table_name="vocabulary_words")
    op.drop_column("vocabulary_words", "list_id")
