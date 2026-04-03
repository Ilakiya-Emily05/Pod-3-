"""Migrate user_id columns from INT to UUID for cross-pod consistency.

Revision ID: c1d2e3f4a5b6
Revises: 885eb5deac10
Create Date: 2026-04-02 18:30:00.000000

"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "c1d2e3f4a5b6"
down_revision: str | Sequence[str] | None = "885eb5deac10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _drop_fk_if_exists(table_name: str, column_name: str) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for fk in inspector.get_foreign_keys(table_name):
        constrained = fk.get("constrained_columns", [])
        name = fk.get("name")
        if column_name in constrained and name:
            op.drop_constraint(name, table_name, type_="foreignkey")


def _int_to_uuid_using_expr(column_name: str) -> str:
    return (
        "CASE "
        f"WHEN {column_name} IS NULL THEN NULL "
        f"ELSE (substr(md5({column_name}::text),1,8) || '-' || "
        f"substr(md5({column_name}::text),9,4) || '-4' || substr(md5({column_name}::text),14,3) || '-' || "
        f"substr('89ab', (get_byte(md5({column_name}::text)::bytea, 0) % 4) + 1, 1) || substr(md5({column_name}::text),18,3) || '-' || "
        f"substr(md5({column_name}::text),21,12))::uuid "
        "END"
    )


def _convert_user_id_column_to_uuid(table_name: str, nullable: bool) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if table_name not in inspector.get_table_names():
        return

    columns = {col["name"]: col for col in inspector.get_columns(table_name)}
    if "user_id" not in columns:
        return

    user_id_col = columns["user_id"]
    user_id_type = user_id_col["type"]

    if isinstance(user_id_type, postgresql.UUID):
        return

    if not isinstance(user_id_type, sa.Integer):
        return

    if table_name in {"test_sessions", "passage_sessions"}:
        _drop_fk_if_exists(table_name, "user_id")

    op.alter_column(
        table_name,
        "user_id",
        existing_type=sa.Integer(),
        type_=postgresql.UUID(as_uuid=True),
        nullable=nullable,
        postgresql_using=_int_to_uuid_using_expr("user_id"),
    )

    if table_name in {"test_sessions", "passage_sessions"}:
        op.create_foreign_key(
            f"fk_{table_name}_user_id_users",
            table_name,
            "users",
            ["user_id"],
            ["id"],
            ondelete=None,
        )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Ensure pronunciation_results exists in Alembic-managed schema.
    if "pronunciation_results" not in inspector.get_table_names():
        op.create_table(
            "pronunciation_results",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("reference_text", sa.String(), nullable=False),
            sa.Column("transcript", sa.String(), nullable=False),
            sa.Column("pronunciation_score", sa.Float(), nullable=False),
            sa.Column("total_mistakes", sa.Integer(), nullable=True),
            sa.Column("mistakes", postgresql.JSON(astext_type=sa.Text()), nullable=True),
            sa.Column("improvement_tips", postgresql.JSON(astext_type=sa.Text()), nullable=True),
            sa.Column("audio_path", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index(
            "ix_pronunciation_results_user_id", "pronunciation_results", ["user_id"], unique=False
        )

    _convert_user_id_column_to_uuid("pronunciation_results", nullable=True)
    _convert_user_id_column_to_uuid("test_sessions", nullable=False)
    _convert_user_id_column_to_uuid("passage_sessions", nullable=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for table_name, nullable in (
        ("passage_sessions", False),
        ("test_sessions", False),
        ("pronunciation_results", True),
    ):
        if table_name not in inspector.get_table_names():
            continue

        columns = {col["name"]: col for col in inspector.get_columns(table_name)}
        if "user_id" not in columns:
            continue
        if not isinstance(columns["user_id"]["type"], postgresql.UUID):
            continue

        if table_name in {"test_sessions", "passage_sessions"}:
            _drop_fk_if_exists(table_name, "user_id")

        # Not reversible to original INT values; sets all UUID values to NULL then casts.
        op.execute(f"UPDATE {table_name} SET user_id = NULL")
        op.alter_column(
            table_name,
            "user_id",
            existing_type=postgresql.UUID(as_uuid=True),
            type_=sa.Integer(),
            nullable=nullable,
            postgresql_using="NULL::integer",
        )

        if table_name in {"test_sessions", "passage_sessions"}:
            op.create_foreign_key(
                f"fk_{table_name}_user_id_users",
                table_name,
                "users",
                ["user_id"],
                ["id"],
                ondelete=None,
            )
