"""
Categories API endpoints - CRUD operations for categories resource.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import List
import logging

from src.core.database import get_db
from src.core.auth import get_current_user, get_admin_user
from src.models.category import Category
from src.models.book import Book
from src.models.user import User, UserRole
from src.schemas.category import (
    CategoryCreate, CategoryUpdate, CategoryResponse,
    CategoryWithBooksResponse, BookCategoriesUpdate
)
from src.schemas.book import BookResponse

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Create a new category.

    Requires Admin privileges.

    Args:
        category: Category data to create
        db: Database session dependency
        current_user: Authenticated admin user

    Returns:
        Created category with ID
    """
    db_category = Category(
        name=category.name,
        description=category.description
    )

    try:
        db.add(db_category)
        db.commit()
        db.refresh(db_category)

        logger.info(f"Successfully created category '{category.name}' (ID: {db_category.id})")
        return db_category

    except IntegrityError as e:
        db.rollback()
        error_message = str(e.orig) if e.orig else str(e)
        logger.error(f"Integrity error creating category: {error_message}")

        if "unique" in error_message.lower() or "duplicate" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with name '{category.name}' already exists"
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity constraint violated"
        )

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating category: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the category"
        )


@router.get("/categories", response_model=List[CategoryResponse], status_code=status.HTTP_200_OK)
async def get_categories(db: Session = Depends(get_db)):
    """
    Get all categories from the database.

    Returns:
        List of all categories
    """
    try:
        categories = db.query(Category).all()
        return categories
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving categories"
        )


@router.get("/categories/{category_id}", response_model=CategoryWithBooksResponse, status_code=status.HTTP_200_OK)
async def get_category(category_id: int, db: Session = Depends(get_db)):
    """
    Get a specific category by ID, including books in this category.

    Args:
        category_id: The ID of the category to retrieve
        db: Database session dependency

    Returns:
        Category details with books
    """
    try:
        category = db.query(Category).options(
            joinedload(Category.books)
        ).filter(Category.id == category_id).first()

        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id {category_id} not found"
            )

        return category
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching category {category_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the category"
        )


@router.put("/categories/{category_id}", response_model=CategoryResponse, status_code=status.HTTP_200_OK)
async def update_category(
    category_id: int,
    category: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Update an existing category.

    Requires Admin privileges.

    Args:
        category_id: The ID of the category to update
        category: Category data to update
        db: Database session dependency
        current_user: Authenticated admin user

    Returns:
        Updated category
    """
    db_category = db.query(Category).filter(Category.id == category_id).first()

    if db_category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )

    # Update only provided fields
    update_data = category.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_category, field, value)

    try:
        db.commit()
        db.refresh(db_category)

        logger.info(f"Successfully updated category ID {category_id}")
        return db_category

    except IntegrityError as e:
        db.rollback()
        error_message = str(e.orig) if e.orig else str(e)
        logger.error(f"Integrity error updating category: {error_message}")

        if "unique" in error_message.lower() or "duplicate" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with name '{category.name}' already exists"
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity constraint violated"
        )

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error updating category {category_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the category"
        )


@router.delete("/categories/{category_id}", status_code=status.HTTP_200_OK)
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Delete a category.

    Requires Admin privileges. Books will be disassociated from the category but not deleted.

    Args:
        category_id: The ID of the category to delete
        db: Database session dependency
        current_user: Authenticated admin user

    Returns:
        Success message
    """
    db_category = db.query(Category).filter(Category.id == category_id).first()

    if db_category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )

    try:
        db.delete(db_category)
        db.commit()

        logger.info(f"Successfully deleted category ID {category_id}")
        return {"message": "Category deleted successfully"}

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error deleting category {category_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the category"
        )


@router.put("/books/{book_id}/categories", response_model=BookResponse, status_code=status.HTTP_200_OK)
async def update_book_categories(
    book_id: int,
    categories_update: BookCategoriesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a book's categories.

    Requires authentication. Owner or Admin can update.

    Args:
        book_id: The ID of the book to update
        categories_update: List of category IDs to assign
        db: Database session dependency
        current_user: Authenticated user

    Returns:
        Updated book
    """
    # Find the book
    db_book = db.query(Book).filter(Book.id == book_id).first()

    if db_book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with id {book_id} not found"
        )

    # Authorization check: Admin OR Owner
    if current_user.role != UserRole.ADMIN and db_book.created_by is not None and db_book.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update categories for your own books"
        )

    # Fetch all requested categories
    categories = db.query(Category).filter(
        Category.id.in_(categories_update.category_ids)
    ).all()

    # Check if all requested categories exist
    found_ids = {cat.id for cat in categories}
    missing_ids = set(categories_update.category_ids) - found_ids
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Categories with ids {list(missing_ids)} not found"
        )

    try:
        # Replace book's categories
        db_book.categories = categories
        db.commit()
        db.refresh(db_book)

        logger.info(f"Successfully updated categories for book ID {book_id}")
        return db_book

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error updating book categories {book_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the book's categories"
        )

