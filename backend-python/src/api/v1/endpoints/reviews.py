"""
Reviews API endpoints - CRUD operations for reviews resource.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import List
import logging

from src.core.database import get_db
from src.core.auth import get_current_user
from src.models.review import Review
from src.models.book import Book
from src.models.user import User, UserRole
from src.schemas.review import ReviewCreate, ReviewResponse, ReviewWithDetailsResponse

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    review: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new review.

    Requires authentication. A user can only review a book once and cannot review their own book.

    Args:
        review: Review data to create
        db: Database session dependency
        current_user: Authenticated user

    Returns:
        Created review with ID
    """
    # Check if book exists
    book = db.query(Book).filter(Book.id == review.book_id).first()
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with id {review.book_id} not found"
        )

    # Check if user is trying to review their own book
    if book.created_by == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot review your own book"
        )

    # Check if user already reviewed this book
    existing_review = db.query(Review).filter(
        Review.book_id == review.book_id,
        Review.user_id == current_user.id
    ).first()

    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reviewed this book"
        )

    db_review = Review(
        book_id=review.book_id,
        user_id=current_user.id,
        rating=review.rating,
        comment=review.comment
    )

    try:
        db.add(db_review)
        db.commit()
        db.refresh(db_review)

        logger.info(f"Successfully created review for book {review.book_id} by user {current_user.id}")
        return db_review

    except IntegrityError as e:
        db.rollback()
        error_message = str(e.orig) if e.orig else str(e)
        logger.error(f"Integrity error creating review: {error_message}")

        # Handle unique constraint violation (shouldn't happen due to pre-check, but just in case)
        if "unique" in error_message.lower() or "duplicate" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already reviewed this book"
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity constraint violated"
        )

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating review: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the review"
        )


@router.get("/books/{book_id}/reviews", response_model=List[ReviewWithDetailsResponse], status_code=status.HTTP_200_OK)
async def get_book_reviews(book_id: int, db: Session = Depends(get_db)):
    """
    Get all reviews for a specific book.

    Args:
        book_id: The ID of the book
        db: Database session dependency

    Returns:
        List of reviews for the book
    """
    # Check if book exists
    book = db.query(Book).filter(Book.id == book_id).first()
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with id {book_id} not found"
        )

    try:
        reviews = db.query(Review).options(
            joinedload(Review.user),
            joinedload(Review.book)
        ).filter(Review.book_id == book_id).all()

        return reviews
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching reviews for book {book_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving reviews"
        )


@router.get("/reviews/{review_id}", response_model=ReviewWithDetailsResponse, status_code=status.HTTP_200_OK)
async def get_review(review_id: int, db: Session = Depends(get_db)):
    """
    Get a specific review by ID.

    Args:
        review_id: The ID of the review
        db: Database session dependency

    Returns:
        Review details
    """
    try:
        review = db.query(Review).options(
            joinedload(Review.user),
            joinedload(Review.book)
        ).filter(Review.id == review_id).first()

        if review is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review with id {review_id} not found"
            )

        return review
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching review {review_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the review"
        )


@router.delete("/reviews/{review_id}", status_code=status.HTTP_200_OK)
async def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a review.

    A user can only delete their own review.

    Args:
        review_id: The ID of the review to delete
        db: Database session dependency
        current_user: Authenticated user

    Returns:
        Success message
    """
    db_review = db.query(Review).filter(Review.id == review_id).first()

    if db_review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review with id {review_id} not found"
        )

    # Check if user owns the review
    if db_review.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own reviews"
        )

    try:
        db.delete(db_review)
        db.commit()

        logger.info(f"Successfully deleted review ID {review_id}")
        return {"message": "Review deleted successfully"}

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error deleting review {review_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the review"
        )

