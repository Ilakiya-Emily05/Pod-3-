"""Finalize Pod 3 UUID cutover for user identity columns.

Revision ID: e4f5a6b7c8d9
Revises: d7f8a9b0c1d2
Create Date: 2026-04-02 19:35:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import context, op

# revision identifiers, used by Alembic.
revision: str = "e4f5a6b7c8d9"
down_revision: str | Sequence[str] | None = "d7f8a9b0c1d2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _column_names(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {col["name"] for col in inspector.get_columns(table_name)}


def _index_names(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {idx["name"] for idx in inspector.get_indexes(table_name)}


def _assert_no_null_uuid_user_ids(table_name: str) -> None:
    count = (
        op.get_bind()
        .execute(sa.text(f"SELECT COUNT(*) FROM {table_name} WHERE uuid_user_id IS NULL"))
        .scalar_one()
    )
    if count > 0:
        raise RuntimeError(
            f"Cannot finalize UUID cutover: {table_name}.uuid_user_id has {count} NULL rows"
        )


def upgrade() -> None:
    if context.is_offline_mode():
        return
    for table_name in ("key_skills", "interview_sessions"):
        if not _table_exists(table_name):
            continue

        cols = _column_names(table_name)
        if "uuid_user_id" not in cols:
            raise RuntimeError(f"{table_name}.uuid_user_id is missing; run prior migration first")

        _assert_no_null_uuid_user_ids(table_name)

        op.alter_column(
            table_name,
            "uuid_user_id",
            existing_type=postgresql.UUID(as_uuid=True),
            nullable=False,
        )

        idx_names = _index_names(table_name)
        legacy_idx = f"ix_{table_name}_user_id"
        if legacy_idx in idx_names:
            op.drop_index(legacy_idx, table_name=table_name)

        if "user_id" in cols:
            op.drop_column(table_name, "user_id")


def downgrade() -> None:
    if context.is_offline_mode():
        return
    for table_name in ("interview_sessions", "key_skills"):
        if not _table_exists(table_name):
            continue

        cols = _column_names(table_name)
        if "user_id" not in cols:
            op.add_column(table_name, sa.Column("user_id", sa.String(), nullable=True))

        # Restore user_id from UUID text to maintain backward compatibility.
        op.execute(
            sa.text(f"UPDATE {table_name} SET user_id = uuid_user_id::text WHERE user_id IS NULL")
        )

        op.alter_column(
            table_name,
            "user_id",
            existing_type=sa.String(),
            nullable=False,
        )

        idx_names = _index_names(table_name)
        legacy_idx = f"ix_{table_name}_user_id"
        if legacy_idx not in idx_names:
            op.create_index(legacy_idx, table_name, ["user_id"], unique=False)

        if "uuid_user_id" in _column_names(table_name):
            op.alter_column(
                table_name,
                "uuid_user_id",
                existing_type=postgresql.UUID(as_uuid=True),
                nullable=True,
            )
