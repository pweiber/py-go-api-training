"""
Statistics API endpoint.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel, Field
from typing import Optional
import logging

from src.core.database import get_db
from src.models.book import Book
from src.models.author import Author
from src.models.category import Category
from src.models.review import Review

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()


class StatsResponse(BaseModel):
    """Schema for statistics response."""
    total_books: int = Field(..., description="Total number of books")
    total_authors: int = Field(..., description="Total number of authors")
    total_categories: int = Field(..., description="Total number of categories")
    total_reviews: int = Field(..., description="Total number of reviews")
    average_rating: Optional[float] = Field(None, description="Average rating across all reviews")


@router.get("/stats", response_model=StatsResponse, status_code=status.HTTP_200_OK)
async def get_statistics(db: Session = Depends(get_db)):
    """
    Get aggregate statistics for the bookstore.

    Returns:
        Statistics including counts and average rating
    """
    try:
        # Get counts
        total_books = db.query(func.count(Book.id)).scalar() or 0
        total_authors = db.query(func.count(Author.id)).scalar() or 0
        total_categories = db.query(func.count(Category.id)).scalar() or 0
        total_reviews = db.query(func.count(Review.id)).scalar() or 0

        # Get average rating
        avg_rating_result = db.query(func.avg(Review.rating)).scalar()
        average_rating = round(float(avg_rating_result), 2) if avg_rating_result else None

        return StatsResponse(
            total_books=total_books,
            total_authors=total_authors,
            total_categories=total_categories,
            total_reviews=total_reviews,
            average_rating=average_rating
        )

    except SQLAlchemyError as e:
        logger.error(f"Database error fetching statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving statistics"
        )

