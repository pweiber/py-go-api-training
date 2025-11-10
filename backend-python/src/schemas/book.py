"""
Pydantic schemas for Book API request/response validation.
"""
from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import Optional


class BookBase(BaseModel):
    """Base schema with common book attributes."""
    title: str = Field(..., min_length=1, max_length=255, description="Book title")
    author: str = Field(..., min_length=1, max_length=255, description="Book author")
    isbn: str = Field(..., min_length=10, max_length=17, description="ISBN-10 or ISBN-13 (with or without dashes)")
    published_date: date = Field(..., description="Publication date")
    description: Optional[str] = Field(None, description="Book description")

    @field_validator('isbn')
    @classmethod
    def normalize_isbn(cls, v: str) -> str:
        """
        Normalize ISBN by removing dashes, spaces, and validating format.
        Accepts ISBN-10 (10 digits) or ISBN-13 (13 digits).
        """
        # Remove dashes and spaces
        cleaned = v.replace('-', '').replace(' ', '')

        # Validate length (ISBN-10 or ISBN-13)
        if len(cleaned) not in [10, 13]:
            raise ValueError(
                f'ISBN must be 10 or 13 characters after removing dashes/spaces. Got {len(cleaned)} characters.'
            )

        # Validate that it contains only digits (allowing 'X' for ISBN-10 check digit)
        if not (cleaned[:-1].isdigit() and (cleaned[-1].isdigit() or (len(cleaned) == 10 and cleaned[-1].upper() == 'X'))):
            raise ValueError('ISBN must contain only digits (ISBN-10 may end with X)')

        return cleaned


class BookCreate(BookBase):
    """Schema for creating a new book."""
    
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
    
    @field_validator('isbn')
    @classmethod
    def normalize_isbn(cls, v: Optional[str]) -> Optional[str]:
        """
        Normalize ISBN by removing dashes, spaces, and validating format.
        Accepts ISBN-10 (10 digits) or ISBN-13 (13 digits).
        """
        if v is None:
            return v

        # Remove dashes and spaces
        cleaned = v.replace('-', '').replace(' ', '')

        # Validate length (ISBN-10 or ISBN-13)
        if len(cleaned) not in [10, 13]:
            raise ValueError(
                f'ISBN must be 10 or 13 characters after removing dashes/spaces. Got {len(cleaned)} characters.'
            )

        # Validate that it contains only digits (allowing 'X' for ISBN-10 check digit)
        if not (cleaned[:-1].isdigit() and (cleaned[-1].isdigit() or (len(cleaned) == 10 and cleaned[-1].upper() == 'X'))):
            raise ValueError('ISBN must contain only digits (ISBN-10 may end with X)')

        return cleaned

    class Config:
        json_schema_extra = {
            "example": {
                "title": "The Advanced Python Guide",
                "description": "An advanced guide to Python programming with best practices"
            }
        }


class BookResponse(BookBase):
    """Schema for book responses, includes the ID."""
    id: int
    
    class Config:
        from_attributes = True  # Allows conversion from SQLAlchemy models
