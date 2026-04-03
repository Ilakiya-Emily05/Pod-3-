"""cleanup_users_table_columns

Revision ID: 33cff6125637
Revises: 12d8fd142f7a
Create Date: 2026-04-03 21:23:45.476374

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '33cff6125637'
down_revision: Union[str, Sequence[str], None] = '12d8fd142f7a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
