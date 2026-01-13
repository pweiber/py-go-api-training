"""Pydantic schemas for Review API request/response validation."""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional


class ReviewBase(BaseModel):
    """Base schema with common review attributes."""
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comment: Optional[str] = Field(None, description="Review comment")


class ReviewCreate(ReviewBase):
    """Schema for creating a new review."""
    book_id: int = Field(..., description="ID of the book being reviewed")

    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v: int) -> int:
        if v < 1 or v > 5:
            raise ValueError('Rating must be between 1 and 5')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "book_id": 1,
                "rating": 5,
                "comment": "An excellent read! Highly recommended."
            }
        }


class ReviewUpdate(BaseModel):
    """Schema for updating a review. All fields are optional."""
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None

    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Rating must be between 1 and 5')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "rating": 4,
                "comment": "Updated review comment"
            }
        }


class ReviewUserResponse(BaseModel):
    """Simplified user schema for review responses."""
    id: int
    email: str

    class Config:
        from_attributes = True


class ReviewBookResponse(BaseModel):
    """Simplified book schema for review responses."""
    id: int
    title: str

    class Config:
        from_attributes = True


class ReviewResponse(ReviewBase):
    """Schema for review responses, includes the ID and relationships."""
    id: int
    book_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewWithDetailsResponse(ReviewResponse):
    """Schema for review response including user and book details."""
    user: ReviewUserResponse
    book: ReviewBookResponse

    class Config:
        from_attributes = True

