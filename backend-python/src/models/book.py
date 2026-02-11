"""
Book model for the bookstore application.
"""
from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, Table, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from src.core.database import Base


# Association table for many-to-many relationship between books and authors
book_authors = Table(
    'book_authors',
    Base.metadata,
    Column('book_id', Integer, ForeignKey('books.id', ondelete='CASCADE'), primary_key=True),
    Column('author_id', Integer, ForeignKey('authors.id', ondelete='CASCADE'), primary_key=True)
)


class Book(Base):
    """
    Book model representing the books table in PostgreSQL.

    Attributes:
        id: Primary key, auto-incrementing integer
        title: Book title (max 255 characters)
        isbn: ISBN number (17 characters, unique)
        published_date: Date when the book was published
        description: Optional text description of the book
        created_by: Foreign key to user who created the book
        creator: Relationship to User model
        authors: Many-to-many relationship to Author model
        categories: Many-to-many relationship to Category model
        reviews: One-to-many relationship to Review model
    """
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    isbn = Column(String(17), unique=True, nullable=False, index=True)
    published_date = Column(Date, nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationship to user (creator)
    creator = relationship("User", back_populates="books")

    # Many-to-many relationship to authors
    authors = relationship("Author", secondary=book_authors, back_populates="books")

    # Many-to-many relationship to categories (using table defined in category.py)
    categories = relationship("Category", secondary="book_categories", back_populates="books")

    # One-to-many relationship to reviews
    reviews = relationship("Review", back_populates="book", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Book(id={self.id}, title='{self.title}', isbn='{self.isbn}')>"
