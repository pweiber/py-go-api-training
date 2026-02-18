"""
Pydantic schemas for Favorite model.
"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class FavoriteResponse(BaseModel):
    """Schema for favorite response."""
    id: int
    user_id: int
    book_id: int
    created_at: datetime

    class Config:
        from_attributes = True
    model_config = ConfigDict(from_attributes=True)


class FavoriteBookResponse(BaseModel):
    """Simplified book schema for favorites list."""
    id: int
    title: str
    isbn: str
    published_date: str
    description: str | None = None

    class Config:
        from_attributes = True
    model_config = ConfigDict(from_attributes=True)


class FavoriteWithBookResponse(BaseModel):
    """Schema for favorite response including book details."""
    id: int
    book_id: int
    created_at: datetime
    book: FavoriteBookResponse

    class Config:
        from_attributes = True
    model_config = ConfigDict(from_attributes=True)

