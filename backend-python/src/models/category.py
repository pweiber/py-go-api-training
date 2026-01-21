"""
Category model for the bookstore application.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Table, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from src.core.database import Base


# Association table for many-to-many relationship between books and categories
book_categories = Table(
    'book_categories',
    Base.metadata,
    Column('book_id', Integer, ForeignKey('books.id', ondelete='CASCADE'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id', ondelete='CASCADE'), primary_key=True)
)


class Category(Base):
    """
    Category model representing the categories table in PostgreSQL.

    Attributes:
        id: Primary key, auto-incrementing integer
        name: Category name (max 100 characters, unique)
        description: Optional category description
        created_at: Timestamp when category was created
        books: Relationship to books in this category (many-to-many)
    """
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Many-to-many relationship to books
    books = relationship("Book", secondary=book_categories, back_populates="categories")

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"

