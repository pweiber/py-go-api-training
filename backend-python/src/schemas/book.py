"""Pydantic schemas for Book API request/response validation."""
from pydantic import BaseModel, Field, field_validator
from datetime import date, datetime
from typing import Optional, List, Generic, TypeVar
from src.schemas.validators import validate_isbn


class BookBase(BaseModel):
    """Base schema with common book attributes."""
    title: str = Field(..., min_length=1, max_length=255, description="Book title")
    isbn: str = Field(..., min_length=10, max_length=17, description="ISBN-10 or ISBN-13 (with or without dashes)")
    published_date: date = Field(..., description="Publication date")
    description: Optional[str] = Field(None, description="Book description")


class BookCreate(BaseModel):
    """Schema for creating a new book."""
    title: str = Field(..., min_length=1, max_length=255, description="Book title")
    isbn: str = Field(..., min_length=10, max_length=17, description="ISBN-10 or ISBN-13")
    published_date: str = Field(..., description="Publication date (YYYY-MM-DD)")
    description: Optional[str] = Field(None, description="Book description")
    author_ids: List[int] = Field(default_factory=list, description="List of author IDs")
    category_ids: List[int] = Field(default_factory=list, description="List of category IDs")

    @field_validator('isbn')
    @classmethod
    def normalize_isbn_on_create(cls, v: str) -> str:
        return validate_isbn(v)

    @field_validator('published_date')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date is in YYYY-MM-DD format."""
        from datetime import datetime
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "The Python Guide",
                "isbn": "978-0-123456-78-9",
                "published_date": "2023-01-15",
                "description": "A comprehensive guide to Python programming",
                "author_ids": [1, 2],
                "category_ids": [3]
            }
        }


class BookUpdate(BaseModel):
    """Schema for updating a book. All fields are optional."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    isbn: Optional[str] = Field(None, min_length=10, max_length=17)
    published_date: Optional[date] = None
    description: Optional[str] = None
    author_ids: Optional[List[int]] = Field(None, description="List of author IDs")
    category_ids: Optional[List[int]] = Field(None, description="List of category IDs")

    @field_validator('isbn')
    @classmethod
    def normalize_isbn_on_update(cls, v: Optional[str]) -> Optional[str]:
        return validate_isbn(v) if v else None

    class Config:
        json_schema_extra = {
            "example": {
                "title": "The Advanced Python Guide",
                "description": "An advanced guide to Python programming with best practices",
                "author_ids": [1, 2],
                "category_ids": [3]
            }
        }


class CategoryInBookResponse(BaseModel):
    """Simplified category schema for book responses."""
    id: int
    name: str

    class Config:
        from_attributes = True


class AuthorInBookResponse(BaseModel):
    """Simplified author schema for book responses."""
    id: int
    name: str

    class Config:
        from_attributes = True


class BookResponse(BookBase):
    """Schema for book responses, includes the ID and creator."""
    id: int
    created_by: Optional[int] = Field(None, description="ID of user who created the book")
    created_at: Optional[datetime] = Field(None, description="Timestamp when book was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when book was last updated")

    @field_validator('isbn')
    @classmethod
    def normalize_isbn_lenient(cls, v: str) -> str:
        try:
            return validate_isbn(v)
        except ValueError:
            return v

    class Config:
        from_attributes = True


class BookWithDetailsResponse(BookResponse):
    """Schema for book response including categories and average rating."""
    categories: List[CategoryInBookResponse] = Field(default_factory=list)
    authors: List[AuthorInBookResponse] = Field(default_factory=list)
    average_rating: Optional[float] = None

    class Config:
        from_attributes = True


T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response schema."""
    items: List[T]
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")

    class Config:
        from_attributes = True
