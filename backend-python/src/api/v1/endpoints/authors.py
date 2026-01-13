"""
Authors API endpoints - CRUD operations for authors resource.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import List
import logging

from src.core.database import get_db
from src.core.auth import get_current_user, get_admin_user
from src.models.author import Author
from src.models.user import User
from src.schemas.author import AuthorCreate, AuthorUpdate, AuthorResponse, AuthorWithBooksResponse

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/authors", response_model=AuthorResponse, status_code=status.HTTP_201_CREATED)
async def create_author(
    author: AuthorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new author.

    Requires authentication.

    Args:
        author: Author data to create
        db: Database session dependency
        current_user: Authenticated user

    Returns:
        Created author with ID
    """
    db_author = Author(
        name=author.name,
        bio=author.bio,
        birth_date=author.birth_date,
        nationality=author.nationality
    )

    try:
        db.add(db_author)
        db.commit()
        db.refresh(db_author)

        logger.info(f"Successfully created author '{author.name}' (ID: {db_author.id})")
        return db_author

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating author: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the author"
        )


@router.get("/authors", response_model=List[AuthorResponse], status_code=status.HTTP_200_OK)
async def get_authors(db: Session = Depends(get_db)):
    """
    Get all authors from the database.

    Returns:
        List of all authors
    """
    try:
        authors = db.query(Author).all()
        return authors
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching authors: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving authors"
        )


@router.get("/authors/{author_id}", response_model=AuthorWithBooksResponse, status_code=status.HTTP_200_OK)
async def get_author(author_id: int, db: Session = Depends(get_db)):
    """
    Get a specific author by ID, including their books.

    Args:
        author_id: The ID of the author to retrieve
        db: Database session dependency

    Returns:
        Author details with their books
    """
    try:
        author = db.query(Author).options(
            joinedload(Author.books)
        ).filter(Author.id == author_id).first()

        if author is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Author with id {author_id} not found"
            )

        return author
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching author {author_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the author"
        )


@router.put("/authors/{author_id}", response_model=AuthorResponse, status_code=status.HTTP_200_OK)
async def update_author(
    author_id: int,
    author: AuthorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing author.

    Requires authentication.

    Args:
        author_id: The ID of the author to update
        author: Author data to update
        db: Database session dependency
        current_user: Authenticated user

    Returns:
        Updated author
    """
    db_author = db.query(Author).filter(Author.id == author_id).first()

    if db_author is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Author with id {author_id} not found"
        )

    # Update only provided fields
    update_data = author.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_author, field, value)

    try:
        db.commit()
        db.refresh(db_author)

        logger.info(f"Successfully updated author ID {author_id}")
        return db_author

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error updating author {author_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the author"
        )


@router.delete("/authors/{author_id}", status_code=status.HTTP_200_OK)
async def delete_author(
    author_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Delete an author.

    Requires Admin privileges. Cannot delete an author who has books.

    Args:
        author_id: The ID of the author to delete
        db: Database session dependency
        current_user: Authenticated admin user

    Returns:
        Success message
    """
    db_author = db.query(Author).options(
        joinedload(Author.books)
    ).filter(Author.id == author_id).first()

    if db_author is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Author with id {author_id} not found"
        )

    # Check if author has books
    if db_author.books and len(db_author.books) > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete author with id {author_id} because they have {len(db_author.books)} book(s). Remove or reassign the books first."
        )

    try:
        db.delete(db_author)
        db.commit()

        logger.info(f"Successfully deleted author ID {author_id}")
        return {"message": "Author deleted successfully"}

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error deleting author {author_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the author"
        )

