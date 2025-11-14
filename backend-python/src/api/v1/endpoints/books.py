"""
Books API endpoints - CRUD operations for books resource.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List

from src.core.database import get_db
from src.core.auth import get_current_user, get_admin_user
from src.models.book import Book
from src.models.user import User
from src.schemas.book import BookCreate, BookUpdate, BookResponse

router = APIRouter()


@router.get("/books", response_model=List[BookResponse], status_code=status.HTTP_200_OK)
async def get_books(db: Session = Depends(get_db)):
    """
    Get all books from the database (public endpoint as per Task 2).
    """
    books = db.query(Book).all()
    # Explicitly validate and return list to avoid serialization issues
    return [BookResponse.model_validate(b) for b in books]


@router.get("/books/{book_id}", response_model=BookResponse, status_code=status.HTTP_200_OK)
async def get_book(book_id: int, db: Session = Depends(get_db)):
    """
    Get a specific book by ID (public endpoint as per Task 2).

    Args:
        book_id: The ID of the book to retrieve
        db: Database session dependency

    Returns:
        Book details
        
    Raises:
        HTTPException: 404 if book not found
    """
    book = db.query(Book).filter(Book.id == book_id).first()
    
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with id {book_id} not found"
        )
    
    return BookResponse.model_validate(book)


@router.post("/books", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    book: BookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new book (requires authentication).

    Args:
        book: Book data to create
        db: Database session dependency
        current_user: Current authenticated user

    Returns:
        Created book with ID and creator information

    Raises:
        HTTPException: 400 if ISBN already exists
        HTTPException: 401 if not authenticated

    Requires:
        Authentication: Bearer token in Authorization header
    """
    # Check if ISBN already exists
    existing_book = db.query(Book).filter(Book.isbn == book.isbn).first()
    if existing_book:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Book with ISBN {book.isbn} already exists"
        )
    
    # Create new book instance with creator
    db_book = Book(
        title=book.title,
        author=book.author,
        isbn=book.isbn,
        published_date=book.published_date,
        description=book.description,
        created_by=current_user.id
    )
    
    # Add to database
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    
    return db_book


@router.put("/books/{book_id}", response_model=BookResponse, status_code=status.HTTP_200_OK)
async def update_book(book_id: int, book: BookUpdate, db: Session = Depends(get_db)):
    """
    Update an existing book (public endpoint as per Task 2).

    Args:
        book_id: The ID of the book to update
        book: Book data to update (only provided fields will be updated)
        db: Database session dependency

    Returns:
        Updated book
        
    Raises:
        HTTPException: 404 if book not found
        HTTPException: 400 if ISBN already exists for another book
    """
    # Find the book
    db_book = db.query(Book).filter(Book.id == book_id).first()
    
    if db_book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with id {book_id} not found"
        )
    
    # Check if ISBN is being updated and if it already exists
    if book.isbn is not None and book.isbn != db_book.isbn:
        existing_book = db.query(Book).filter(Book.isbn == book.isbn).first()
        if existing_book:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Book with ISBN {book.isbn} already exists"
            )
    
    # Update only provided fields
    update_data = book.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_book, field, value)
    
    db.commit()
    db.refresh(db_book)
    
    return db_book


@router.delete("/books/{book_id}", status_code=status.HTTP_200_OK)
async def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Delete a book (requires admin role).

    Args:
        book_id: The ID of the book to delete
        db: Database session dependency
        admin_user: Current authenticated admin user

    Returns:
        Success message
        
    Raises:
        HTTPException: 404 if book not found
        HTTPException: 403 if user is not admin

    Requires:
        Authentication: Bearer token with admin role
    """
    # Find the book
    db_book = db.query(Book).filter(Book.id == book_id).first()
    
    if db_book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with id {book_id} not found"
        )
    
    # Delete the book
    db.delete(db_book)
    db.commit()
    
    return {"message": "Book deleted successfully"}
