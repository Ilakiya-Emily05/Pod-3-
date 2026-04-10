"""Convert pronunciation_results id to UUID primary key.

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-04-04 10:15:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "h8i9j0k1l2m3"
down_revision: str | Sequence[str] | None = "g7h8i9j0k1l2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    columns = {col["name"] for col in inspector.get_columns(table_name)}
    return column_name in columns


def upgrade() -> None:
    """Convert pronunciation_results.id from INT to UUID."""

    if not _table_exists("pronunciation_results"):
        return

    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # Add new UUID column
    if not _column_exists("pronunciation_results", "new_id"):
        op.add_column(
            "pronunciation_results",
            sa.Column(
                "new_id",
                postgresql.UUID(as_uuid=True),
                server_default=sa.text("gen_random_uuid()"),
                nullable=False,
            ),
        )

    # Drop old primary key and drop autoincrement sequence
    op.drop_constraint("pronunciation_results_pkey", "pronunciation_results", type_="primary")

    # Drop the old id column
    op.drop_column("pronunciation_results", "id")

    # Rename new_id to id using alter_column
    op.alter_column("pronunciation_results", "new_id", new_column_name="id")

    # Create new primary key
    op.create_primary_key("pronunciation_results_pkey", "pronunciation_results", ["id"])

    # Create indexes
    op.execute("DROP INDEX IF EXISTS ix_pronunciation_results_id")
    op.execute("DROP INDEX IF EXISTS ix_pronunciation_results_user_id")
    op.create_index("ix_pronunciation_results_user_id", "pronunciation_results", ["user_id"])


def downgrade() -> None:
    """Revert pronunciation_results.id back to INTEGER."""

    raise NotImplementedError(
        "Downgrading from UUID to INTEGER primary keys is not supported for pronunciation_results. "
        "Please restore from database backup if rollback is required."
    )
