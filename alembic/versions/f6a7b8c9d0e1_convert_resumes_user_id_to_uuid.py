"""Convert resumes.user_id to UUID.

Revision ID: f6a7b8c9d0e1
Revises: e4f5a6b7c8d9
Create Date: 2026-04-04 08:25:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f6a7b8c9d0e1"
down_revision: str | Sequence[str] | None = "e4f5a6b7c8d9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


UUID_REGEX = (
    "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _column_names(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {col["name"] for col in inspector.get_columns(table_name)}


def upgrade() -> None:
    if not _table_exists("resumes"):
        return

    cols = _column_names("resumes")
    if "user_id" not in cols:
        return

    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.execute(
        sa.text(
            f"""
            UPDATE resumes
            SET user_id = gen_random_uuid()::text
            WHERE user_id IS NULL OR user_id !~* '{UUID_REGEX}'
            """
        )
    )

    op.alter_column(
        "resumes",
        "user_id",
        existing_type=sa.String(length=50),
        type_=postgresql.UUID(as_uuid=True),
        nullable=False,
        postgresql_using="user_id::uuid",
    )


def downgrade() -> None:
    if not _table_exists("resumes") or "user_id" not in _column_names("resumes"):
        return

    op.alter_column(
        "resumes",
        "user_id",
        existing_type=postgresql.UUID(as_uuid=True),
        type_=sa.String(length=50),
        nullable=False,
        postgresql_using="user_id::text",
    )
