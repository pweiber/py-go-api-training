"""
Pydantic schemas for User authentication and management.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional
from src.models.user import UserRole


class UserBase(BaseModel):
    """Base schema with common user attributes."""
    email: EmailStr = Field(..., description="User email address")


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=100, description="User password (min 8 characters)")

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isalpha() for char in v):
            raise ValueError("Password must contain at least one letter")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "testpassword123"
            }
        }


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "testpassword123"
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

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        """Validate password strength if provided."""
        if v is None:
            return v
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isalpha() for char in v):
            raise ValueError("Password must contain at least one letter")
        return v


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
    email: Optional[str] = None
    user_id: Optional[int] = None


class UserRoleUpdate(BaseModel):
    """Schema for updating user role (admin-only)."""
    role: UserRole = Field(..., description="New user role")

    class Config:
        json_schema_extra = {
            "example": {
                "role": "admin"
            }
        }


