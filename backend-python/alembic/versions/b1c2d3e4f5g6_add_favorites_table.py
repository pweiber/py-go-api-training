"""add_favorites_table

Revision ID: b1c2d3e4f5g6
Revises: 03865bb3abd0
Create Date: 2025-02-13 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b1c2d3e4f5g6'
down_revision = '03865bb3abd0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema - Add favorites table."""
    op.create_table('favorites',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('book_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'book_id', name='uq_user_book_favorite')
    )
    op.create_index(op.f('ix_favorites_id'), 'favorites', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema - Drop favorites table."""
    op.drop_index(op.f('ix_favorites_id'), table_name='favorites')
    op.drop_table('favorites')

