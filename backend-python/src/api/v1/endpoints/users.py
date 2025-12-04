"""
User Management API endpoints - Admin-only user role management.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.auth import get_admin_user
from src.models.user import User, UserRole
from src.schemas.user import UserRoleUpdate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.patch("/{user_id}/role", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user_role(
    user_id: int,
    role_update: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Update user role (admin-only).
    
    Allows administrators to promote users to admin or demote them to regular user.
    Only users with admin role can access this endpoint.
    
    Args:
        user_id: The ID of the user to update
        role_update: New role information
        db: Database session dependency
        current_user: Current authenticated admin user
        
    Returns:
        Updated user information
        
    Raises:
        HTTPException: 404 if user not found
        HTTPException: 403 if current user is not admin
        HTTPException: 400 if trying to demote the last admin
        
    Requires:
        Authentication: Bearer token with admin role
        
    Example Request:
        PATCH /users/5/role
        Headers: Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
        {
            "role": "admin"
        }
        
    Example Response (200):
        {
            "id": 5,
            "email": "user@example.com",
            "is_active": true,
            "role": "admin",
            "created_at": "2023-09-12T10:30:00.123456"
        }
    """
    # Find the user to update
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Prevent demoting the last admin
    if user.role == UserRole.ADMIN and role_update.role == UserRole.USER:
        admin_count = db.query(User).filter(User.role == UserRole.ADMIN).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the last admin user. Promote another user to admin first."
            )
    
    # Update the user's role
    user.role = role_update.role
    db.commit()
    db.refresh(user)
    
    return user


@router.get("", response_model=list[UserResponse], status_code=status.HTTP_200_OK)
async def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    List all users (admin-only).
    
    Returns a list of all registered users in the system.
    Only users with admin role can access this endpoint.
    
    Args:
        db: Database session dependency
        current_user: Current authenticated admin user
        
    Returns:
        List of all users
        
    Requires:
        Authentication: Bearer token with admin role
        
    Example Request:
        GET /users
        Headers: Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
        
    Example Response (200):
        [
            {
                "id": 1,
                "email": "admin@example.com",
                "is_active": true,
                "role": "admin",
                "created_at": "2023-09-12T10:30:00.123456"
            },
            {
                "id": 2,
                "email": "user@example.com",
                "is_active": true,
                "role": "user",
                "created_at": "2023-09-12T11:00:00.123456"
            }
        ]
    """
    users = db.query(User).all()
    return users


@router.get("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Get user by ID (admin-only).
    
    Returns detailed information about a specific user.
    Only users with admin role can access this endpoint.
    
    Args:
        user_id: The ID of the user to retrieve
        db: Database session dependency
        current_user: Current authenticated admin user
        
    Returns:
        User information
        
    Raises:
        HTTPException: 404 if user not found
        
    Requires:
        Authentication: Bearer token with admin role
        
    Example Request:
        GET /users/5
        Headers: Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
        
    Example Response (200):
        {
            "id": 5,
            "email": "user@example.com",
            "is_active": true,
            "role": "user",
            "created_at": "2023-09-12T10:30:00.123456"
        }
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    return user

