"""standardize_user_id_to_uuid

Revision ID: uuid_std_001
Revises: 1ee1c906bb02
Create Date: 2026-04-02 21:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'uuid_std_001'
down_revision: Union[str, None] = '1ee1c906bb02'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Dummy UUID for orphaned/legacy records
DUMMY_UUID = '00000000-0000-0000-0000-000000000000'

def upgrade() -> None:
    # Postgres regex for UUID
    UUID_REGEX = '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'

    # 1. Standardize 'resumes'
    op.execute(f"UPDATE resumes SET user_id = '{DUMMY_UUID}' WHERE user_id !~ '{UUID_REGEX}'")
    op.alter_column('resumes', 'user_id',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.String(length=36),
               existing_nullable=False)
    
    # 2. Standardize 'key_skills'
    op.execute(f"UPDATE key_skills SET user_id = '{DUMMY_UUID}' WHERE user_id !~ '{UUID_REGEX}'")
    op.execute("ALTER TABLE key_skills ALTER COLUMN user_id TYPE UUID USING user_id::uuid")
    
    # 3. Standardize 'interview_sessions'
    op.execute(f"UPDATE interview_sessions SET user_id = '{DUMMY_UUID}' WHERE user_id !~ '{UUID_REGEX}'")
    op.execute("ALTER TABLE interview_sessions ALTER COLUMN user_id TYPE UUID USING user_id::uuid")


def downgrade() -> None:
    # Reverse migrations
    op.execute("ALTER TABLE interview_sessions ALTER COLUMN user_id TYPE VARCHAR")
    op.execute("ALTER TABLE key_skills ALTER COLUMN user_id TYPE VARCHAR")
    op.alter_column('resumes', 'user_id',
               existing_type=sa.String(length=36),
               type_=sa.VARCHAR(length=50),
               existing_nullable=False)
