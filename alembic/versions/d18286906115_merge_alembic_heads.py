"""merge alembic heads

Revision ID: d18286906115
Revises: b0fd3c343aa2, h8i9j0k1l2m3
Create Date: 2026-04-08 16:05:11.655612

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "d18286906115"
down_revision: str | Sequence[str] | None = ("b0fd3c343aa2", "h8i9j0k1l2m3")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
