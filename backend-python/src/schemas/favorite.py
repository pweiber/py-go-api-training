"""
Pydantic schemas for Favorite model.
"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime, date


class FavoriteResponse(BaseModel):
    """Schema for favorite response."""
    id: int
    user_id: int
    book_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FavoriteBookResponse(BaseModel):
    """Simplified book schema for favorites list."""
    id: int
    title: str
    isbn: str
    published_date: date
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


class FavoriteWithBookResponse(BaseModel):
    """Schema for favorite response including book details."""
    id: int
    book_id: int
    created_at: datetime
    book: FavoriteBookResponse

    model_config = ConfigDict(from_attributes=True)

class FavoriteCreateResponse(BaseModel):
    """Schema for favorite creation response."""
    message: str
    id: int
    book_id: int

    model_config = ConfigDict(from_attributes=True)