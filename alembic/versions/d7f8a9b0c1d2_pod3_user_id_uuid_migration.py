"""Pod 3 user_id UUID migration with legacy mapping table.

Revision ID: d7f8a9b0c1d2
Revises: c1d2e3f4a5b6
Create Date: 2026-04-02 19:05:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d7f8a9b0c1d2"
down_revision: str | Sequence[str] | None = "c1d2e3f4a5b6"
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
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "user_id_mapping",
        sa.Column("legacy_int_id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("uuid_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
    )

    for table_name in ("key_skills", "interview_sessions"):
        if not _table_exists(table_name):
            continue
        if "uuid_user_id" not in _column_names(table_name):
            op.add_column(
                table_name,
                sa.Column("uuid_user_id", postgresql.UUID(as_uuid=True), nullable=True),
            )

    # Build legacy INT -> UUID map from Pod-3 string user_id values where user_id is numeric.
    op.execute(
        """
        INSERT INTO user_id_mapping (legacy_int_id, uuid_id)
        SELECT DISTINCT CAST(user_id AS INTEGER), gen_random_uuid()
        FROM (
            SELECT user_id FROM key_skills WHERE user_id ~ '^[0-9]+$'
            UNION
            SELECT user_id FROM interview_sessions WHERE user_id ~ '^[0-9]+$'
        ) src
        ON CONFLICT (legacy_int_id) DO NOTHING
        """
    )

    # Backfill from existing UUID-looking user_id strings.
    op.execute(
        f"""
        UPDATE key_skills
        SET uuid_user_id = user_id::uuid
        WHERE uuid_user_id IS NULL
          AND user_id IS NOT NULL
          AND user_id ~* '{UUID_REGEX}'
        """
    )
    op.execute(
        f"""
        UPDATE interview_sessions
        SET uuid_user_id = user_id::uuid
        WHERE uuid_user_id IS NULL
          AND user_id IS NOT NULL
          AND user_id ~* '{UUID_REGEX}'
        """
    )

    # Backfill from mapping table for numeric legacy IDs.
    op.execute(
        """
        UPDATE key_skills ks
        SET uuid_user_id = m.uuid_id
        FROM user_id_mapping m
        WHERE ks.uuid_user_id IS NULL
          AND ks.user_id ~ '^[0-9]+$'
          AND m.legacy_int_id = CAST(ks.user_id AS INTEGER)
        """
    )
    op.execute(
        """
        UPDATE interview_sessions s
        SET uuid_user_id = m.uuid_id
        FROM user_id_mapping m
        WHERE s.uuid_user_id IS NULL
          AND s.user_id ~ '^[0-9]+$'
          AND m.legacy_int_id = CAST(s.user_id AS INTEGER)
        """
    )

    op.create_index("ix_key_skills_uuid_user_id", "key_skills", ["uuid_user_id"], unique=False)
    op.create_index(
        "ix_interview_sessions_uuid_user_id",
        "interview_sessions",
        ["uuid_user_id"],
        unique=False,
    )


def downgrade() -> None:
    if _table_exists("interview_sessions"):
        op.drop_index("ix_interview_sessions_uuid_user_id", table_name="interview_sessions")
        if "uuid_user_id" in _column_names("interview_sessions"):
            op.drop_column("interview_sessions", "uuid_user_id")

    if _table_exists("key_skills"):
        op.drop_index("ix_key_skills_uuid_user_id", table_name="key_skills")
        if "uuid_user_id" in _column_names("key_skills"):
            op.drop_column("key_skills", "uuid_user_id")

    op.drop_table("user_id_mapping")
