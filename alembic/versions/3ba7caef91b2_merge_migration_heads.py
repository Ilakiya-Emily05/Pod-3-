"""merge_migration_heads

Revision ID: 3ba7caef91b2
Revises: 885eb5deac10, 459f2e3351f5
Create Date: 2026-04-03 23:54:28.798689

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3ba7caef91b2'
down_revision: Union[str, Sequence[str], None] = ('885eb5deac10', '459f2e3351f5')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
