"""
Authentication API endpoints - User registration, login, and profile management.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import timedelta

from src.core.database import get_db
from src.core.auth import (
    hash_password,
    authenticate_user,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from src.models.user import User
from src.schemas.user import UserCreate, UserLogin, UserResponse, UserUpdate, Token

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    Creates a new user account with email validation and password hashing.
    
    Args:
        user: User registration data (email, password, role)
        db: Database session dependency
        
    Returns:
        Created user information (without password)
        
    Raises:
        HTTPException: 400 if email already registered
        
    Example Request:
        POST /register
        {
            "email": "user@example.com",
            "password": "testpassword123",
            "role": "user"
        }
        
    Example Response (201):
        {
            "id": 1,
            "email": "user@example.com",
            "is_active": true,
            "role": "user",
            "created_at": "2023-09-12T10:30:00.123456"
        }
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email {user.email} already exists"
        )
    
    # Create new user with hashed password
    db_user = User(
        email=user.email,
        hashed_password=hash_password(user.password),
        role=user.role,
        is_active=True
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login user and return JWT access token.
    
    Authenticates user credentials and returns a JWT token for subsequent requests.
    
    Args:
        user_credentials: User login credentials (email, password)
        db: Database session dependency
        
    Returns:
        JWT access token and token type
        
    Raises:
        HTTPException: 401 if credentials are invalid
        
    Example Request:
        POST /login
        {
            "email": "user@example.com",
            "password": "testpassword123"
        }
        
    Example Response (200):
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer"
        }
    """
    # Authenticate user
    user = authenticate_user(db, user_credentials.email, user_credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "role": user.role.value},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user profile.
    
    Returns the profile information of the currently authenticated user.
    
    Args:
        current_user: Current authenticated user from JWT token
        
    Returns:
        Current user profile information
        
    Requires:
        Authentication: Bearer token in Authorization header
        
    Example Request:
        GET /me
        Headers: Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
        
    Example Response (200):
        {
            "id": 1,
            "email": "user@example.com",
            "is_active": true,
            "role": "user",
            "created_at": "2023-09-12T10:30:00.123456"
        }
    """
    return current_user


@router.put("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user profile.
    
    Updates the profile information of the currently authenticated user.
    
    Args:
        user_update: Updated user information (email, password, is_active)
        current_user: Current authenticated user from JWT token
        db: Database session dependency
        
    Returns:
        Updated user profile information
        
    Raises:
        HTTPException: 400 if email already exists
        
    Requires:
        Authentication: Bearer token in Authorization header
        
    Example Request:
        PUT /me
        Headers: Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
        {
            "email": "newemail@example.com"
        }
        
    Example Response (200):
        {
            "id": 1,
            "email": "newemail@example.com",
            "is_active": true,
            "role": "user",
            "created_at": "2023-09-12T10:30:00.123456"
        }
    """
    # Check if email is being updated and if it already exists
    if user_update.email and user_update.email != current_user.email:
        existing_user = db.query(User).filter(User.email == user_update.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email {user_update.email} already in use"
            )
    
    # Update user fields
    update_data = user_update.model_dump(exclude_unset=True)
    
    # Hash password if it's being updated
    if "password" in update_data:
        update_data["hashed_password"] = hash_password(update_data.pop("password"))
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user

