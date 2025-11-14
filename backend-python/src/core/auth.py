    Example:
        @app.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user)):
            return {"message": f"Hello {current_user.email}"}
    """
    token = credentials.credentials
    token_data = verify_token(token)
    
    user = db.query(User).filter(User.email == token_data.email).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Verify that the current user has admin role.
    
    This is a FastAPI dependency that ensures only admin users can access
    certain routes.
    
    Args:
        current_user: Current authenticated user from get_current_user dependency
        
    Returns:
        User object if user is an admin
        
    Raises:
        HTTPException: 403 if user is not an admin
        
    Example:
        @app.delete("/books/{id}")
        async def delete_book(
            id: int,
            admin_user: User = Depends(get_admin_user)
        ):
            # Only admins can delete books
            pass
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin role required."
        )
    
    return current_user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user by email and password.
    
    Args:
        db: Database session
        email: User email address
        password: Plain text password
        
    Returns:
        User object if authentication successful, None otherwise
        
    Example:
        >>> user = authenticate_user(db, "user@example.com", "password123")
        >>> user.email if user else None
        'user@example.com'
    """
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user
"""
Authentication utilities for JWT token generation and validation.
Includes password hashing and user verification.
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.database import get_db
from src.models.user import User, UserRole
from src.schemas.user import TokenData

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# HTTP Bearer security scheme
security = HTTPBearer()


def hash_password(password: str) -> str:
    """
    Hash a plain password using bcrypt.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password string
        
    Example:
        >>> hashed = hash_password("mypassword123")
        >>> len(hashed) > 0
        True
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
        
    Example:
        >>> hashed = hash_password("mypassword123")
        >>> verify_password("mypassword123", hashed)
        True
        >>> verify_password("wrongpassword", hashed)
        False
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary containing claims to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
        
    Example:
        >>> token = create_access_token({"sub": "user@example.com", "user_id": 1})
        >>> len(token) > 0
        True
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string to verify
        
    Returns:
        TokenData object containing decoded claims
        
    Raises:
        HTTPException: If token is invalid or expired
        
    Example:
        >>> token = create_access_token({"sub": "user@example.com", "user_id": 1})
        >>> token_data = verify_token(token)
        >>> token_data.email == "user@example.com"
        True
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        
        if email is None:
            raise credentials_exception
            
        token_data = TokenData(email=email, user_id=user_id)
        return token_data
        
    except JWTError:
        raise credentials_exception


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token.
    
    This is a FastAPI dependency that extracts the JWT token from the
    Authorization header, validates it, and returns the corresponding user.
    
    Args:
        credentials: HTTP Bearer credentials containing the JWT token
        db: Database session dependency
        
    Returns:
        User object of the authenticated user
        
    Raises:
        HTTPException: 401 if token is invalid or user not found
        HTTPException: 403 if user is inactive
        

