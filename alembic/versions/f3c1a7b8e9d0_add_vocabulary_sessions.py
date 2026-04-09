"""add vocabulary sessions

Revision ID: f3c1a7b8e9d0
Revises: 83b909912715
Create Date: 2026-04-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f3c1a7b8e9d0'
down_revision: Union[str, Sequence[str], None] = '83b909912715'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'vocabulary_sessions',
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('vocabulary_sessions_user_id_fkey')),
        sa.PrimaryKeyConstraint('session_id', name=op.f('vocabulary_sessions_pkey')),
    )
    op.create_index(op.f('ix_vocabulary_sessions_user_id'), 'vocabulary_sessions', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_vocabulary_sessions_user_id'), table_name='vocabulary_sessions')
    op.drop_table('vocabulary_sessions')