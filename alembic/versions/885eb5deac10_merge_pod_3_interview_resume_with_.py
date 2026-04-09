"""Merge Pod-3 Interview/Resume with original root

Revision ID: 885eb5deac10
Revises: 1ee1c906bb02, 6cf5cdad4292
Create Date: 2026-04-01 22:20:18.452042

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "885eb5deac10"
down_revision: str | Sequence[str] | None = ("1ee1c906bb02", "6cf5cdad4292")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
