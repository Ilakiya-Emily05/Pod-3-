"""merge_pod3_sentence_framing_heads

Revision ID: 07f91239dc91
Revises: b0fd3c343aa2, h8i9j0k1l2m3
Create Date: 2026-04-08 18:23:40.453975

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "07f91239dc91"
down_revision: str | Sequence[str] | None = ("b0fd3c343aa2", "h8i9j0k1l2m3")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
