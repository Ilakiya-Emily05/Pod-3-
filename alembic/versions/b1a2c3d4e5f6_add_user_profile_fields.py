"""add user profile fields

Revision ID: b1a2c3d4e5f6
Revises: 1b2c3d4e5f6a
Create Date: 2026-04-16 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b1a2c3d4e5f6"
down_revision: str | Sequence[str] | None = "1b2c3d4e5f6a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("name", sa.String(length=255), nullable=False, server_default=sa.text("''")),
    )
    op.add_column(
        "users",
        sa.Column("learning_goal", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("learning_frequency", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("streak_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "users",
        sa.Column("total_xp", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "users",
        sa.Column("last_active_date", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "last_active_date")
    op.drop_column("users", "total_xp")
    op.drop_column("users", "streak_count")
    op.drop_column("users", "learning_frequency")
    op.drop_column("users", "learning_goal")
    op.drop_column("users", "name")
