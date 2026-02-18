"""
Favorite model for user's favorite books.
"""
from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from datetime import datetime, timezone
from sqlalchemy.orm import relationship

from src.core.database import Base


class Favorite(Base):
    """
    Favorite model representing the favorites table.

    Represents many-to-many relationship between users and books
    for tracking which books a user has favorited.

    Attributes:
        id: Primary key, auto-incrementing integer
        user_id: Foreign key to users table
        book_id: Foreign key to books table
        created_at: Timestamp when favorite was added
        user: Relationship to User model
        book: Relationship to Book model
    """
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime (timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="favorites")
    book = relationship("Book", back_populates="favorited_by")

    # Unique constraint: a user can only favorite a book once
    __table_args__ = (
        UniqueConstraint('user_id', 'book_id', name='uq_user_book_favorite'),
    )

    def __repr__(self):
        return f"<Favorite(id={self.id}, user_id={self.user_id}, book_id={self.book_id})>"

