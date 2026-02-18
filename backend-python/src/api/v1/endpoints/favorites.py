"""
Favorites API endpoints - Add/remove/list favorite books.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import List
import logging

from src.core.database import get_db
from src.core.auth import get_current_user
from src.models.favorite import Favorite
from src.models.book import Book
from src.models.user import User
from src.schemas.favorite import FavoriteWithBookResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/books/{book_id}/favorite", status_code=status.HTTP_201_CREATED)
async def add_favorite(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a book to user's favorites."""
    book = db.query(Book).filter(Book.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Book with id {book_id} not found")

    existing = db.query(Favorite).filter(Favorite.user_id == current_user.id, Favorite.book_id == book_id).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already favorited this book")

    favorite = Favorite(user_id=current_user.id, book_id=book_id)
    try:
        db.add(favorite)
        db.commit()
        db.refresh(favorite)
        logger.info(f"User {current_user.id} favorited book {book_id}")
        return {"message": "Book added to favorites", "id": favorite.id, "book_id": favorite.book_id}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already favorited this book")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error adding favorite: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred")


@router.delete("/books/{book_id}/favorite", status_code=status.HTTP_200_OK)
async def remove_favorite(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a book from user's favorites."""
    favorite = db.query(Favorite).filter(Favorite.user_id == current_user.id, Favorite.book_id == book_id).first()
    if favorite is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Book {book_id} is not in your favorites")

    try:
        db.delete(favorite)
        db.commit()
        logger.info(f"User {current_user.id} removed favorite for book {book_id}")
        return {"message": "Book removed from favorites"}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error removing favorite: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred")


@router.get("/users/me/favorites", response_model=List[FavoriteWithBookResponse], status_code=status.HTTP_200_OK)
async def get_my_favorites(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get current user's favorite books."""
    try:
        favorites = db.query(Favorite).options(
            joinedload(Favorite.book).joinedload(Book.authors),
            joinedload(Favorite.book).joinedload(Book.categories),
            joinedload(Favorite.book).joinedload(Book.reviews)
        ).filter(Favorite.user_id == current_user.id).all()

        logger.info(f"Retrieved {len(favorites)} favorites for user {current_user.id}")
        return favorites
    except SQLAlchemyError as e:
        logger.error(f"Error fetching favorites: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred")

