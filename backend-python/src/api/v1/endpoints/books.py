"""
Books API endpoints - CRUD operations for books resource.

This module implements RESTful CRUD operations for the Book resource with
comprehensive error handling for database operations.
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import func, or_
from typing import List, Optional
import logging
import math

from src.core.database import get_db
from src.core.auth import get_current_user, get_admin_user
from src.models.book import Book
from src.models.category import Category
from src.models.review import Review
from src.models.user import User, UserRole
from src.schemas.book import BookCreate, BookUpdate, BookResponse, BookWithDetailsResponse, PaginatedResponse

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/books", response_model=PaginatedResponse[BookWithDetailsResponse], status_code=status.HTTP_200_OK)
async def get_books(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description="Search in title and description"),
    author_id: Optional[int] = Query(None, description="Filter by author ID"),
    category: Optional[str] = Query(None, description="Filter by category name"),
    min_rating: Optional[float] = Query(None, ge=1, le=5, description="Minimum average rating"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page")
):
    """
    Get all books from the database with filtering and pagination.

    Args:
        db: Database session dependency
        search: Optional search term for title/description
        author_id: Optional filter by author ID
        category: Optional filter by category name
        min_rating: Optional minimum average rating filter
        page: Page number (default 1)
        size: Items per page (default 10, max 100)

    Returns:
        Paginated list of books with details

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        # Subquery to calculate average rating per book (use for all books, not just when filtering)
        rating_subquery = db.query(
            Review.book_id,
            func.avg(Review.rating).label('avg_rating')
        ).group_by(Review.book_id).subquery()

        # Base query with eager loading to avoid N+1 and include average rating
        query = db.query(Book, rating_subquery.c.avg_rating).outerjoin(
            rating_subquery,
            Book.id == rating_subquery.c.book_id
        ).options(
            selectinload(Book.categories),
            selectinload(Book.author_rel)
        )

        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Book.title.ilike(search_term),
                    Book.description.ilike(search_term)
                )
            )

        # Apply author filter
        if author_id:
            query = query.filter(Book.author_id == author_id)

        # Apply category filter
        if category:
            query = query.join(Book.categories).filter(Category.name.ilike(category))

        # Apply min_rating filter
        if min_rating is not None:
            query = query.filter(rating_subquery.c.avg_rating >= min_rating)

        # Get total count before pagination
        total = query.count()

        # Calculate pagination
        pages = math.ceil(total / size) if total > 0 else 1
        offset = (page - 1) * size

        # Apply pagination
        results = query.offset(offset).limit(size).all()

        # Build response with database-calculated average rating
        items = []
        for book, avg_rating in results:
            book_dict = {
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "author_id": book.author_id,
                "isbn": book.isbn,
                "published_date": book.published_date,
                "description": book.description,
                "created_by": book.created_by,
                "categories": book.categories,
                "author_rel": book.author_rel,
                "average_rating": round(avg_rating, 2) if avg_rating is not None else None
            }

            items.append(BookWithDetailsResponse.model_validate(book_dict))

        return PaginatedResponse[BookWithDetailsResponse](
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )

    except SQLAlchemyError as e:
        logger.error(f"Database error fetching books: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving books"
        )


@router.get("/books/{book_id}", response_model=BookWithDetailsResponse, status_code=status.HTTP_200_OK)
async def get_book(book_id: int, db: Session = Depends(get_db)):
    """
    Get a specific book by ID.
    
    Args:
        book_id: The ID of the book to retrieve
        db: Database session dependency
        
    Returns:
        Book details with categories and average rating

    Raises:
        HTTPException: 404 if book not found
        HTTPException: 500 if database error occurs
    """
    try:
        # Subquery to calculate average rating
        rating_subquery = db.query(
            Review.book_id,
            func.avg(Review.rating).label('avg_rating')
        ).group_by(Review.book_id).subquery()

        # Query book with average rating from database
        result = db.query(Book, rating_subquery.c.avg_rating).outerjoin(
            rating_subquery,
            Book.id == rating_subquery.c.book_id
        ).options(
            selectinload(Book.categories),
            selectinload(Book.author_rel)
        ).filter(Book.id == book_id).first()

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Book with id {book_id} not found"
            )

        book, avg_rating = result

        return BookWithDetailsResponse(
            id=book.id,
            title=book.title,
            author=book.author,
            author_id=book.author_id,
            isbn=book.isbn,
            published_date=book.published_date,
            description=book.description,
            created_by=book.created_by,
            categories=book.categories,
            author_rel=book.author_rel,
            average_rating=round(avg_rating, 2) if avg_rating is not None else None
        )
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
        author_id=book.author_id,
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
    
    Authorization Rules:
        - Admin users can update any book
        - Regular users can only update books they created
        - Legacy books (created_by=None) can only be updated by admins
          (maintained for backward compatibility with pre-auth books)

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
    # Note: Legacy books with created_by=None can only be updated by admins
    # since (None != current_user.id) will always be True for non-admin users
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
