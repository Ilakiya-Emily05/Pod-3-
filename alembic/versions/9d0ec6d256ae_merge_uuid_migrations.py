"""Merge UUID migrations

Revision ID: 9d0ec6d256ae
Revises: 4ffd209d425d, e4f5a6b7c8d9
Create Date: 2026-04-04 07:47:15.546661

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9d0ec6d256ae'
down_revision: Union[str, Sequence[str], None] = ('4ffd209d425d', 'e4f5a6b7c8d9')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
