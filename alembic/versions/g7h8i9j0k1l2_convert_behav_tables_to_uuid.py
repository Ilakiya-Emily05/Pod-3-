"""Convert behavioral assessment tables to use UUID primary keys.

Revision ID: g7h8i9j0k1l2
Revises: f6a7b8c9d0e1
Create Date: 2026-04-04 09:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "g7h8i9j0k1l2"
down_revision: str | Sequence[str] | None = "f6a7b8c9d0e1"
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
    """Convert behav_questions, behav_options, behav_option_scores, behav_user_answers to UUID."""

    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # behav_questions: id INT -> UUID
    if _table_exists("behav_questions"):
        if not _column_exists("behav_questions", "new_id"):
            op.add_column(
                "behav_questions",
                sa.Column(
                    "new_id",
                    postgresql.UUID(as_uuid=True),
                    server_default=sa.text("gen_random_uuid()"),
                    nullable=False,
                ),
            )
        # Backfill mapping: keep old id to new_id relationship for FK updates
        op.execute(
            """
            CREATE TEMP TABLE behav_questions_mapping AS
            SELECT id, new_id FROM behav_questions
            """
        )

    # behav_options: id INT -> UUID, question_id INT -> UUID (FK)
    if _table_exists("behav_options"):
        if not _column_exists("behav_options", "new_id"):
            op.add_column(
                "behav_options",
                sa.Column(
                    "new_id",
                    postgresql.UUID(as_uuid=True),
                    server_default=sa.text("gen_random_uuid()"),
                    nullable=False,
                ),
            )
        if not _column_exists("behav_options", "new_question_id"):
            op.add_column(
                "behav_options",
                sa.Column("new_question_id", postgresql.UUID(as_uuid=True), nullable=True),
            )
        # Map question_id to new UUID values
        op.execute(
            """
            UPDATE behav_options bo
            SET new_question_id = bqm.new_id
            FROM behav_questions_mapping bqm
            WHERE bo.question_id = bqm.id
            """
        )

    # behav_option_scores: id INT -> UUID, option_id INT -> UUID (FK)
    if _table_exists("behav_option_scores"):
        if not _column_exists("behav_option_scores", "new_id"):
            op.add_column(
                "behav_option_scores",
                sa.Column(
                    "new_id",
                    postgresql.UUID(as_uuid=True),
                    server_default=sa.text("gen_random_uuid()"),
                    nullable=False,
                ),
            )
        if not _column_exists("behav_option_scores", "new_option_id"):
            op.add_column(
                "behav_option_scores",
                sa.Column("new_option_id", postgresql.UUID(as_uuid=True), nullable=True),
            )
        # Create temp mapping for options
        op.execute(
            """
            CREATE TEMP TABLE behav_options_mapping AS
            SELECT id, new_id FROM behav_options
            """
        )
        # Map option_id to new UUID values
        op.execute(
            """
            UPDATE behav_option_scores bos
            SET new_option_id = bom.new_id
            FROM behav_options_mapping bom
            WHERE bos.option_id = bom.id
            """
        )

    # behav_user_answers: id INT -> UUID, question_id INT -> UUID, option_id INT -> UUID
    if _table_exists("behav_user_answers"):
        if not _column_exists("behav_user_answers", "new_id"):
            op.add_column(
                "behav_user_answers",
                sa.Column(
                    "new_id",
                    postgresql.UUID(as_uuid=True),
                    server_default=sa.text("gen_random_uuid()"),
                    nullable=False,
                ),
            )
        if not _column_exists("behav_user_answers", "new_question_id"):
            op.add_column(
                "behav_user_answers",
                sa.Column("new_question_id", postgresql.UUID(as_uuid=True), nullable=True),
            )
        if not _column_exists("behav_user_answers", "new_option_id"):
            op.add_column(
                "behav_user_answers",
                sa.Column("new_option_id", postgresql.UUID(as_uuid=True), nullable=True),
            )
        # Map FKs
        op.execute(
            """
            UPDATE behav_user_answers bua
            SET new_question_id = bqm.new_id
            FROM behav_questions_mapping bqm
            WHERE bua.question_id = bqm.id
            """
        )
        op.execute(
            """
            UPDATE behav_user_answers bua
            SET new_option_id = bom.new_id
            FROM behav_options_mapping bom
            WHERE bua.option_id = bom.id
            """
        )

    # Drop old FKs before column changes
    if _table_exists("behav_options"):
        op.execute(
            "ALTER TABLE behav_options DROP CONSTRAINT IF EXISTS behav_options_question_id_fkey"
        )

    if _table_exists("behav_option_scores"):
        op.execute(
            "ALTER TABLE behav_option_scores DROP CONSTRAINT IF EXISTS behav_option_scores_option_id_fkey"
        )

    if _table_exists("behav_user_answers"):
        op.execute(
            "ALTER TABLE behav_user_answers DROP CONSTRAINT IF EXISTS behav_user_answers_question_id_fkey"
        )
        op.execute(
            "ALTER TABLE behav_user_answers DROP CONSTRAINT IF EXISTS behav_user_answers_option_id_fkey"
        )

    # Drop old columns and create new structure
    if _table_exists("behav_questions"):
        op.execute("DROP INDEX IF EXISTS ix_behav_questions_id")
        op.drop_constraint("behav_questions_pkey", "behav_questions", type_="primary")
        op.drop_column("behav_questions", "id")
        op.alter_column("behav_questions", "new_id", new_column_name="id")
        op.create_primary_key("behav_questions_pkey", "behav_questions", ["id"])

    if _table_exists("behav_options"):
        op.execute("DROP INDEX IF EXISTS ix_behav_options_id")
        op.drop_constraint("behav_options_pkey", "behav_options", type_="primary")
        op.drop_column("behav_options", "id")
        op.drop_column("behav_options", "question_id")
        op.alter_column("behav_options", "new_id", new_column_name="id")
        op.alter_column("behav_options", "new_question_id", new_column_name="question_id")
        op.create_primary_key("behav_options_pkey", "behav_options", ["id"])
        op.alter_column("behav_options", "question_id", nullable=False)
        op.create_foreign_key(
            "behav_options_question_id_fkey",
            "behav_options",
            "behav_questions",
            ["question_id"],
            ["id"],
        )
        op.create_index("ix_behav_options_question_id", "behav_options", ["question_id"])

    if _table_exists("behav_option_scores"):
        op.execute("DROP INDEX IF EXISTS ix_behav_option_scores_id")
        op.execute("DROP INDEX IF EXISTS ix_behav_option_scores_option_id")
        op.drop_constraint("behav_option_scores_pkey", "behav_option_scores", type_="primary")
        op.drop_column("behav_option_scores", "id")
        op.drop_column("behav_option_scores", "option_id")
        op.alter_column("behav_option_scores", "new_id", new_column_name="id")
        op.alter_column("behav_option_scores", "new_option_id", new_column_name="option_id")
        op.create_primary_key("behav_option_scores_pkey", "behav_option_scores", ["id"])
        op.alter_column("behav_option_scores", "option_id", nullable=False)
        op.create_foreign_key(
            "behav_option_scores_option_id_fkey",
            "behav_option_scores",
            "behav_options",
            ["option_id"],
            ["id"],
        )
        op.create_index("ix_behav_option_scores_option_id", "behav_option_scores", ["option_id"])

    if _table_exists("behav_user_answers"):
        op.execute("DROP INDEX IF EXISTS ix_behav_user_answers_id")
        op.execute("DROP INDEX IF EXISTS ix_behav_user_answers_question_id")
        op.execute("DROP INDEX IF EXISTS ix_behav_user_answers_option_id")
        op.drop_constraint("behav_user_answers_pkey", "behav_user_answers", type_="primary")
        op.drop_column("behav_user_answers", "id")
        op.drop_column("behav_user_answers", "question_id")
        op.drop_column("behav_user_answers", "option_id")
        op.alter_column("behav_user_answers", "new_id", new_column_name="id")
        op.alter_column("behav_user_answers", "new_question_id", new_column_name="question_id")
        op.alter_column("behav_user_answers", "new_option_id", new_column_name="option_id")
        op.create_primary_key("behav_user_answers_pkey", "behav_user_answers", ["id"])
        op.alter_column("behav_user_answers", "question_id", nullable=False)
        op.alter_column("behav_user_answers", "option_id", nullable=False)
        op.create_foreign_key(
            "behav_user_answers_question_id_fkey",
            "behav_user_answers",
            "behav_questions",
            ["question_id"],
            ["id"],
        )
        op.create_foreign_key(
            "behav_user_answers_option_id_fkey",
            "behav_user_answers",
            "behav_options",
            ["option_id"],
            ["id"],
        )
        op.create_index("ix_behav_user_answers_question_id", "behav_user_answers", ["question_id"])
        op.create_index("ix_behav_user_answers_option_id", "behav_user_answers", ["option_id"])


def downgrade() -> None:
    """Revert behavioral assessment tables back to integer primary keys."""

    raise NotImplementedError(
        "Downgrading from UUID to INTEGER primary keys is not supported for behavioral tables. "
        "Please restore from database backup if rollback is required."
    )
