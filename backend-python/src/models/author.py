"""
Author model for the bookstore application.
"""
from sqlalchemy import Column, Integer, String, Date, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from src.core.database import Base


class Author(Base):
    """
    Author model representing the authors table in PostgreSQL.

    Attributes:
        id: Primary key, auto-incrementing integer
        name: Author's full name (max 255 characters)
        bio: Optional biography text
        birth_date: Author's date of birth
        nationality: Author's nationality (max 100 characters)
        created_at: Timestamp when author was created
        books: Many-to-many relationship to books by this author
    """
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    bio = Column(Text, nullable=True)
    birth_date = Column(Date, nullable=True)
    nationality = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Many-to-many relationship to books (uses book_authors table defined in book.py)
    books = relationship("Book", secondary="book_authors", back_populates="authors")

    def __repr__(self):
        return f"<Author(id={self.id}, name='{self.name}')>"
