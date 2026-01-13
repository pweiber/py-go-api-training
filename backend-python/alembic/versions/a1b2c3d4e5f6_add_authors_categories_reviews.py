"""Add authors, categories, reviews tables and relationships

Revision ID: a1b2c3d4e5f6
Revises: 882207e0fa6a
Create Date: 2026-01-12 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], str] = '882207e0fa6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create authors table
    op.create_table('authors',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('birth_date', sa.Date(), nullable=True),
        sa.Column('nationality', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_authors_id'), 'authors', ['id'], unique=False)
    op.create_index(op.f('ix_authors_name'), 'authors', ['name'], unique=False)

    # Create categories table
    op.create_table('categories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_categories_id'), 'categories', ['id'], unique=False)
    op.create_index(op.f('ix_categories_name'), 'categories', ['name'], unique=False)

    # Create reviews table
    op.create_table('reviews',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('book_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('book_id', 'user_id', name='uq_review_book_user'),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='ck_review_rating_range')
    )
    op.create_index(op.f('ix_reviews_id'), 'reviews', ['id'], unique=False)
    op.create_index(op.f('ix_reviews_book_id'), 'reviews', ['book_id'], unique=False)
    op.create_index(op.f('ix_reviews_user_id'), 'reviews', ['user_id'], unique=False)

    # Create book_categories association table (many-to-many)
    op.create_table('book_categories',
        sa.Column('book_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('book_id', 'category_id')
    )
    op.create_index(op.f('ix_book_categories_book_id'), 'book_categories', ['book_id'], unique=False)
    op.create_index(op.f('ix_book_categories_category_id'), 'book_categories', ['category_id'], unique=False)

    # Add author_id foreign key to books table
    op.add_column('books', sa.Column('author_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_books_author_id', 'books', 'authors', ['author_id'], ['id'], ondelete='SET NULL')
    op.create_index(op.f('ix_books_author_id'), 'books', ['author_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove author_id from books
    op.drop_index(op.f('ix_books_author_id'), table_name='books')
    op.drop_constraint('fk_books_author_id', 'books', type_='foreignkey')
    op.drop_column('books', 'author_id')

    # Drop book_categories association table
    op.drop_index(op.f('ix_book_categories_category_id'), table_name='book_categories')
    op.drop_index(op.f('ix_book_categories_book_id'), table_name='book_categories')
    op.drop_table('book_categories')

    # Drop reviews table
    op.drop_index(op.f('ix_reviews_user_id'), table_name='reviews')
    op.drop_index(op.f('ix_reviews_book_id'), table_name='reviews')
    op.drop_index(op.f('ix_reviews_id'), table_name='reviews')
    op.drop_table('reviews')

    # Drop categories table
    op.drop_index(op.f('ix_categories_name'), table_name='categories')
    op.drop_index(op.f('ix_categories_id'), table_name='categories')
    op.drop_table('categories')

    # Drop authors table
    op.drop_index(op.f('ix_authors_name'), table_name='authors')
    op.drop_index(op.f('ix_authors_id'), table_name='authors')
    op.drop_table('authors')

