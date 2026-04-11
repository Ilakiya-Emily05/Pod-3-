"""create learning path tables

Revision ID: 1b2c3d4e5f6a
Revises: 9a0b1c2d3e4f, a268bfa65a15
Create Date: 2026-04-11 17:05:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1b2c3d4e5f6a"
down_revision: str | Sequence[str] | None = ("9a0b1c2d3e4f", "a268bfa65a15")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "learning_paths",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cefr_level", sa.String(length=10), nullable=False),
        sa.Column("assigned_modules", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("user_goal", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_learning_paths_user_id"), "learning_paths", ["user_id"], unique=False)

    op.create_table(
        "module_unlocks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("module_name", sa.String(length=50), nullable=False),
        sa.Column("unlocked_level", sa.String(length=20), nullable=False),
        sa.Column("unlocked_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_module_unlocks_user_id"), "module_unlocks", ["user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_module_unlocks_user_id"), table_name="module_unlocks")
    op.drop_table("module_unlocks")
    op.drop_index(op.f("ix_learning_paths_user_id"), table_name="learning_paths")
    op.drop_table("learning_paths")
