"""merge alembic heads

Revision ID: a268bfa65a15
Revises: 47f856dff7dd, d18286906115
Create Date: 2026-04-08 21:46:30.596115

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "a268bfa65a15"
down_revision: str | Sequence[str] | None = ("47f856dff7dd", "d18286906115")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
