"""Convert interview_system table IDs and FKs to proper UUID type

Revision ID: 47f856dff7dd
Revises: 07f91239dc91
Create Date: 2026-04-08 18:26:45.126146

"""

import contextlib
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "47f856dff7dd"
down_revision: str | Sequence[str] | None = "07f91239dc91"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - convert questions and user_responses to native UUID type."""
    # Drop any existing foreign key constraints first
    with contextlib.suppress(BaseException):
        op.drop_constraint("user_responses_question_id_fkey", "user_responses", type_="foreignkey")
    with contextlib.suppress(BaseException):
        op.drop_constraint("user_responses_session_id_fkey", "user_responses", type_="foreignkey")

    # Alter questions.id column type to UUID
    op.execute("ALTER TABLE questions ALTER COLUMN id TYPE uuid USING (id::uuid)")
    op.execute("ALTER TABLE questions ALTER COLUMN skill_id TYPE uuid USING (skill_id::uuid)")

    # Alter user_responses columns to UUID
    op.execute("ALTER TABLE user_responses ALTER COLUMN id TYPE uuid USING (id::uuid)")
    op.execute(
        "ALTER TABLE user_responses ALTER COLUMN session_id TYPE uuid USING (session_id::uuid)"
    )
    op.execute(
        "ALTER TABLE user_responses ALTER COLUMN question_id TYPE uuid USING (question_id::uuid)"
    )

    # Recreate foreign key constraints
    op.create_foreign_key(
        "user_responses_session_id_fkey",
        "user_responses",
        "interview_sessions",
        ["session_id"],
        ["id"],
    )
    op.create_foreign_key(
        "user_responses_question_id_fkey", "user_responses", "questions", ["question_id"], ["id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
