"""
Pydantic schemas for Book API request/response validation.
"""
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class BookBase(BaseModel):
    """Base schema with common book attributes."""
    title: str = Field(..., min_length=1, max_length=255, description="Book title")
    author: str = Field(..., min_length=1, max_length=255, description="Book author")
    isbn: str = Field(..., min_length=10, max_length=20, description="ISBN number (with or without dashes)")
    published_date: date = Field(..., description="Publication date")
    description: Optional[str] = Field(None, description="Book description")


class BookCreate(BookBase):
    """Schema for creating a new book."""
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "The Python Guide",
                "author": "John Doe",
                "isbn": "978-0123456789",
                "published_date": "2023-01-15",
                "description": "A comprehensive guide to Python programming"
            }
        }


class BookUpdate(BaseModel):
    """Schema for updating a book. All fields are optional."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    author: Optional[str] = Field(None, min_length=1, max_length=255)
    isbn: Optional[str] = Field(None, min_length=10, max_length=20)
    published_date: Optional[date] = None
    description: Optional[str] = None
    
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
