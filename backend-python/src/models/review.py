"""
Review model for the bookstore application.
"""
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from src.core.database import Base


class Review(Base):
    """
    Review model representing the reviews table in PostgreSQL.

    Attributes:
        id: Primary key, auto-incrementing integer
        book_id: Foreign key to the reviewed book
        user_id: Foreign key to the user who wrote the review
        rating: Rating from 1 to 5
        comment: Optional review text
        created_at: Timestamp when review was created
        book: Relationship to Book model
        user: Relationship to User model
    """
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey('books.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    book = relationship("Book", back_populates="reviews")
    user = relationship("User", back_populates="reviews")

    # Constraints
    __table_args__ = (
        UniqueConstraint('book_id', 'user_id', name='uq_review_book_user'),
        CheckConstraint('rating >= 1 AND rating <= 5', name='ck_review_rating_range'),
    )

    def __repr__(self):
        return f"<Review(id={self.id}, book_id={self.book_id}, user_id={self.user_id}, rating={self.rating})>"

