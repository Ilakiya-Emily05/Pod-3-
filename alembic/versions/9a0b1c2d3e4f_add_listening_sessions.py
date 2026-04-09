"""add listening sessions

Revision ID: 9a0b1c2d3e4f
Revises: f3c1a7b8e9d0
Create Date: 2026-04-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9a0b1c2d3e4f'
down_revision: Union[str, Sequence[str], None] = 'f3c1a7b8e9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'listening_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('passage', sa.Text(), nullable=False),
        sa.Column('questions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('user_transcript', sa.Text(), nullable=True),
        sa.Column('similarity_score', sa.Float(), nullable=True),
        sa.Column('audio_filename', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('listening_sessions_pkey')),
        sa.UniqueConstraint('session_id', name=op.f('uq_listening_sessions_session_id')),
    )
    op.create_index(op.f('ix_listening_sessions_session_id'), 'listening_sessions', ['session_id'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_listening_sessions_session_id'), table_name='listening_sessions')
    op.drop_table('listening_sessions')