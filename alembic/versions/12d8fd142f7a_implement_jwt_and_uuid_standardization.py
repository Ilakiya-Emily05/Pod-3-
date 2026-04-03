"""implement_jwt_and_uuid_standardization

Revision ID: 12d8fd142f7a
Revises: uuid_std_001
Create Date: 2026-04-03 20:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '12d8fd142f7a'
down_revision: Union[str, None] = 'uuid_std_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create or Update Users table
    # Check if table exists (Alembic usually handles this, but we'll be explicit about additions)
    # Based on autogenerate, it seems users table exists but needs modification
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'users' not in tables:
        op.create_table('users',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('email', sa.String(), nullable=False),
            sa.Column('hashed_password', sa.String(), nullable=False),
            sa.Column('role', sa.String(), nullable=False, server_default='user'),
            sa.Column('oauth_provider', sa.String(), nullable=True),
            sa.Column('profile_completed', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    else:
        # Table exists, add missing columns/alter existing
        existing_cols = [c['name'] for c in inspector.get_columns('users')]
        if 'hashed_password' not in existing_cols:
            op.add_column('users', sa.Column('hashed_password', sa.String(), nullable=True))
            # If we had data, we'd need to migrate it. Assuming fresh start for these specific pod-3 auth requirements.
        if 'role' not in existing_cols:
            op.add_column('users', sa.Column('role', sa.String(), nullable=False, server_default='user'))
        if 'profile_completed' not in existing_cols:
            op.add_column('users', sa.Column('profile_completed', sa.Boolean(), nullable=False, server_default='false'))
        if 'oauth_provider' not in existing_cols:
            op.add_column('users', sa.Column('oauth_provider', sa.String(), nullable=True))
        
        # Ensure ID is UUID
        op.execute("ALTER TABLE users ALTER COLUMN id TYPE UUID USING id::uuid")

    # 2. Standardize Resumes table to UUID
    op.execute("ALTER TABLE resumes ALTER COLUMN id TYPE UUID USING id::uuid")
    op.execute("ALTER TABLE resumes ALTER COLUMN user_id TYPE UUID USING user_id::uuid")
    
    # 3. Ensure other Interview System tables are UUID (they should be, but let's be safe)
    op.execute("ALTER TABLE key_skills ALTER COLUMN id TYPE UUID USING id::uuid")
    op.execute("ALTER TABLE key_skills ALTER COLUMN user_id TYPE UUID USING user_id::uuid")
    
    op.execute("ALTER TABLE questions ALTER COLUMN id TYPE UUID USING id::uuid")
    op.execute("ALTER TABLE questions ALTER COLUMN skill_id TYPE UUID USING skill_id::uuid")
    
    op.execute("ALTER TABLE interview_sessions ALTER COLUMN id TYPE UUID USING id::uuid")
    op.execute("ALTER TABLE interview_sessions ALTER COLUMN user_id TYPE UUID USING user_id::uuid")
    
    op.execute("ALTER TABLE user_responses ALTER COLUMN id TYPE UUID USING id::uuid")
    if 'session_id' in [c['name'] for c in inspector.get_columns('user_responses')]:
        op.execute("ALTER TABLE user_responses ALTER COLUMN session_id TYPE UUID USING session_id::uuid")
    op.execute("ALTER TABLE user_responses ALTER COLUMN question_id TYPE UUID USING question_id::uuid")


def downgrade() -> None:
    # Downgrade is complex for UUID conversion, usually involves going back to String
    op.execute("ALTER TABLE resumes ALTER COLUMN id TYPE VARCHAR(36)")
    op.execute("ALTER TABLE resumes ALTER COLUMN user_id TYPE VARCHAR(36)")
    # Other tables were already UUID or intended to be.
    pass
