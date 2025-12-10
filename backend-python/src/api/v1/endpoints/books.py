"""
Books API endpoints - CRUD operations for books resource.

This module implements RESTful CRUD operations for the Book resource with
comprehensive error handling for database operations.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import List
import logging

from src.core.database import get_db
from src.core.auth import get_current_user, get_admin_user
from src.models.book import Book
from src.models.user import User, UserRole
from src.schemas.book import BookCreate, BookUpdate, BookResponse

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/books", response_model=List[BookResponse], status_code=status.HTTP_200_OK)
async def get_books(db: Session = Depends(get_db)):
    """
    Get all books from the database.
    
    Args:
        db: Database session dependency
        
    Returns:
        List of all books

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        books = db.query(Book).all()
        return books
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching books: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving books"
        )


@router.get("/books/{book_id}", response_model=BookResponse, status_code=status.HTTP_200_OK)
async def get_book(book_id: int, db: Session = Depends(get_db)):
    """
    Get a specific book by ID.
    
    Args:
        book_id: The ID of the book to retrieve
        db: Database session dependency
        
    Returns:
        Book details
        
    Raises:
        HTTPException: 404 if book not found
        HTTPException: 500 if database error occurs
    """
    try:
        book = db.query(Book).filter(Book.id == book_id).first()

        if book is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Book with id {book_id} not found"
            )

        return book
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching book {book_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the book"
        )


@router.post("/books", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    book: BookCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new book.
    
    Requires authentication. The creating user is recorded as the owner.
    
    Args:
        book: Book data to create
        db: Database session dependency
        current_user: Authenticated user creating the book
        
    Returns:
        Created book with ID
        
    Raises:
        HTTPException: 400 if ISBN already exists
        HTTPException: 500 if database error occurs
    """
    # Create new book instance
    db_book = Book(
        title=book.title,
        author=book.author,
        isbn=book.isbn,
        published_date=book.published_date,
        description=book.description,
        created_by=current_user.id
    )
    
    # Add to database with exception handling
    try:
        db.add(db_book)
        db.commit()
        db.refresh(db_book)

        logger.info(f"Successfully created book with ISBN {book.isbn} (ID: {db_book.id}) by User {current_user.id}")
        return db_book

    except IntegrityError as e:
        db.rollback()
        error_message = str(e.orig) if e.orig else str(e)
        logger.error(f"Integrity error creating book: {error_message}")

        # Handle duplicate ISBN constraint violation
        if "isbn" in error_message.lower() and ("unique" in error_message.lower() or "duplicate" in error_message.lower()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Book with ISBN {book.isbn} already exists"
            )

        # Handle other integrity errors (NOT NULL, CHECK constraints, etc.)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity constraint violated"
        )

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating book: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the book"
        )


@router.put("/books/{book_id}", response_model=BookResponse, status_code=status.HTTP_200_OK)
async def update_book(
    book_id: int, 
    book: BookUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing book.
    
    Requires authentication. Only the Owner or an Admin can update a book.
    
    Args:
        book_id: The ID of the book to update
        book: Book data to update
        db: Database session dependency
        current_user: Authenticated user requesting update
        
    Returns:
        Updated book
        
    Raises:
        HTTPException: 404 if book not found
        HTTPException: 403 if user is not authorized to update this book
        HTTPException: 400 if ISBN conflict
        HTTPException: 500 if database error occurs
    """
    # Find the book
    db_book = db.query(Book).filter(Book.id == book_id).first()
    
    if db_book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with id {book_id} not found"
        )
    
    # Authorization check: Admin OR Owner
    if current_user.role != UserRole.ADMIN and db_book.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own books"
        )
    
    # Update only provided fields
    update_data = book.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_book, field, value)
    
    # Commit with exception handling
    try:
        db.commit()
        db.refresh(db_book)

        logger.info(f"Successfully updated book ID {book_id}")
        return db_book

    except IntegrityError as e:
        db.rollback()
        error_message = str(e.orig) if e.orig else str(e)
        logger.error(f"Integrity error updating book {book_id}: {error_message}")

        # Handle duplicate ISBN constraint violation
        if "isbn" in error_message.lower() and ("unique" in error_message.lower() or "duplicate" in error_message.lower()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Book with ISBN {book.isbn} already exists"
            )

        # Handle other integrity errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity constraint violated"
        )

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error updating book {book_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the book"
        )


@router.delete("/books/{book_id}", status_code=status.HTTP_200_OK)
async def delete_book(
    book_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Delete a book.
    
    Requires Admin privileges.
    
    Args:
        book_id: The ID of the book to delete
        db: Database session dependency
        current_user: Authenticated admin user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: 404 if book not found
        HTTPException: 409 if book is referenced by other records
        HTTPException: 500 if database error occurs
    """
    # Find the book
    db_book = db.query(Book).filter(Book.id == book_id).first()
    
    if db_book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with id {book_id} not found"
        )
    
    # Delete with exception handling
    try:
        db.delete(db_book)
        db.commit()

        logger.info(f"Successfully deleted book ID {book_id}")
        return {"message": "Book deleted successfully"}

    except IntegrityError as e:
        db.rollback()
        error_message = str(e.orig) if e.orig else str(e)
        logger.error(f"Integrity error deleting book {book_id}: {error_message}")

        # Handle foreign key constraint (book is referenced elsewhere)
        if "foreign key" in error_message.lower() or "referenced" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete book because it is referenced by other records (e.g., orders, reviews)"
            )

        # Handle other integrity errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete book due to database constraints"
        )

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error deleting book {book_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the book"
        )
