"""Pydantic schemas for Author API request/response validation."""
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, List


class AuthorBase(BaseModel):
    """Base schema with common author attributes."""
    name: str = Field(..., min_length=1, max_length=255, description="Author's full name")
    bio: Optional[str] = Field(None, description="Author's biography")
    birth_date: Optional[date] = Field(None, description="Author's date of birth")
    nationality: Optional[str] = Field(None, max_length=100, description="Author's nationality")


class AuthorCreate(AuthorBase):
    """Schema for creating a new author."""

    class Config:
        json_schema_extra = {
            "example": {
                "name": "J.K. Rowling",
                "bio": "British author best known for the Harry Potter series",
                "birth_date": "1965-07-31",
                "nationality": "British"
            }
        }


class AuthorUpdate(BaseModel):
    """Schema for updating an author. All fields are optional."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    bio: Optional[str] = None
    birth_date: Optional[date] = None
    nationality: Optional[str] = Field(None, max_length=100)

    class Config:
        json_schema_extra = {
            "example": {
                "bio": "Updated biography text"
            }
        }


class AuthorResponse(AuthorBase):
    """Schema for author responses, includes the ID and created_at."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class BookInAuthorResponse(BaseModel):
    """Simplified book schema for author responses."""
    id: int
    title: str
    isbn: str
    published_date: date

    class Config:
        from_attributes = True


class AuthorWithBooksResponse(AuthorResponse):
    """Schema for author response including their books."""
    books: List[BookInAuthorResponse] = []

    class Config:
        from_attributes = True

