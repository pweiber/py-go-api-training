"""Pydantic schemas for Category API request/response validation."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class CategoryBase(BaseModel):
    """Base schema with common category attributes."""
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, description="Category description")


class CategoryCreate(CategoryBase):
    """Schema for creating a new category."""

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Fantasy",
                "description": "Fantasy and magical fiction books"
            }
        }


class CategoryUpdate(BaseModel):
    """Schema for updating a category. All fields are optional."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "description": "Updated category description"
            }
        }


class CategoryResponse(CategoryBase):
    """Schema for category responses, includes the ID and created_at."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class BookInCategoryResponse(BaseModel):
    """Simplified book schema for category responses."""
    id: int
    title: str
    isbn: str

    class Config:
        from_attributes = True


class CategoryWithBooksResponse(CategoryResponse):
    """Schema for category response including books in this category."""
    books: List[BookInCategoryResponse] = []

    class Config:
        from_attributes = True


class BookCategoriesUpdate(BaseModel):
    """Schema for updating a book's categories."""
    category_ids: List[int] = Field(..., description="List of category IDs to assign to the book")

    class Config:
        json_schema_extra = {
            "example": {
                "category_ids": [1, 2, 3]
            }
        }

