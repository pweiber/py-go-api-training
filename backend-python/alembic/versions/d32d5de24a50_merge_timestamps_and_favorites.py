"""merge_timestamps_and_favorites

Revision ID: d32d5de24a50
Revises: da1126c22739, b1c2d3e4f5g6
Create Date: 2026-02-25 13:02:39.632208

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd32d5de24a50'
down_revision: Union[str, Sequence[str], None] = ('da1126c22739', 'b1c2d3e4f5g6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
