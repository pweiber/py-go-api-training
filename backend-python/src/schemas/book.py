"""Pydantic schemas for Book API request/response validation."""
from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import Optional
from src.schemas.validators import validate_isbn


class BookBase(BaseModel):
    """Base schema with common book attributes."""
    title: str = Field(..., min_length=1, max_length=255, description="Book title")
    author: str = Field(..., min_length=1, max_length=255, description="Book author")
    isbn: str = Field(..., min_length=10, max_length=17, description="ISBN-10 or ISBN-13 (with or without dashes)")
    published_date: date = Field(..., description="Publication date")
    description: Optional[str] = Field(None, description="Book description")

    # NOTE: Intentionally no validator here so responses don't re-validate
    # existing DB data (avoids 500 if legacy rows contain invalid ISBN).


class BookCreate(BookBase):
    """Schema for creating a new book."""

    # Validate/normalize only on input (creation)
    @field_validator('isbn')
    @classmethod
    def normalize_isbn_on_create(cls, v: str) -> str:
        return validate_isbn(v)

    class Config:
        json_schema_extra = {
            "example": {
                "title": "The Python Guide",
                "author": "John Doe",
                "isbn": "9780123456789",  # Can also accept "978-0-12-345678-9" format
                "published_date": "2023-01-15",
                "description": "A comprehensive guide to Python programming"
            }
        }


class BookUpdate(BaseModel):
    """Schema for updating a book. All fields are optional."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    author: Optional[str] = Field(None, min_length=1, max_length=255)
    isbn: Optional[str] = Field(None, min_length=10, max_length=17)
    published_date: Optional[date] = None
    description: Optional[str] = None

    # Validate/normalize only on input (update)
    @field_validator('isbn')
    @classmethod
    def normalize_isbn_on_update(cls, v: Optional[str]) -> Optional[str]:
        return validate_isbn(v)

    class Config:
        json_schema_extra = {
            "example": {
                "title": "The Advanced Python Guide",
                "description": "An advanced guide to Python programming with best practices"
            }
        }


class BookResponse(BookBase):
    """Schema for book responses, includes the ID and creator."""
    id: int
    created_by: Optional[int] = Field(None, description="ID of user who created the book")

    @field_validator('isbn')
    @classmethod
    def normalize_isbn_lenient(cls, v: str) -> str:
        #Attempt to normalize ISBN without raising errors for legacy data
        try:
            return validate_isbn(v)
        except ValueError:
            # Return as-is if validation fails (legacy data)
            return v

    class Config:
        from_attributes = True  # Allows conversion from SQLAlchemy models
