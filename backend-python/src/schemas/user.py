"""
Pydantic schemas for User authentication and management.
"""
import re
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional
from src.models.user import UserRole
from src.schemas.validators import validate_password_strength


class UserBase(BaseModel):
    """Base schema with common user attributes."""
    email: EmailStr = Field(..., description="User email address")


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=100, description="User password (min 8 characters)")

    @field_validator('email')
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email to lowercase."""
        return v.lower().strip()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        result = validate_password_strength(v)
        if result is None:
            raise ValueError("Password is required")
        return result

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "TestPassword123!"
            }
        }


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    @field_validator('email')
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email to lowercase."""
        return v.lower().strip()

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "TestPassword123!"
            }
        }


class UserResponse(BaseModel):
    """Schema for user response (excludes password)."""
    id: int = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email address")
    is_active: bool = Field(..., description="Whether user is active")
    role: UserRole = Field(..., description="User role")
    created_at: datetime = Field(..., description="User creation timestamp")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "is_active": True,
                "role": "user",
                "created_at": "2023-09-12T10:30:00.123456"
            }
        }


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    email: Optional[EmailStr] = Field(None, description="User email address")
    password: Optional[str] = Field(None, min_length=8, max_length=100, description="New password")
    is_active: Optional[bool] = Field(None, description="Whether user is active")
    current_password: Optional[str] = Field(None, description="Current password (required for email change)")

    @field_validator('email')
    @classmethod
    def normalize_email(cls, v: Optional[str]) -> Optional[str]:
        """Normalize email to lowercase if provided."""
        if v is None:
            return v
        return v.lower().strip()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        """Validate password strength if provided."""
        return validate_password_strength(v)

class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }


class TokenData(BaseModel):
    """Schema for decoded token data."""
    email: str = Field(..., description="User email from JWT token")
    user_id: int = Field(..., description="User ID from JWT token")


class UserRoleUpdate(BaseModel):
    """Schema for updating user role (admin-only)."""
    role: UserRole = Field(..., description="New user role")

    class Config:
        json_schema_extra = {
            "example": {
                "role": "admin"
            }
        }


