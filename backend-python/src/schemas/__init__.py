"""Pydantic schemas package for request/response validation."""
from src.schemas.book import (
    BookCreate, BookUpdate, BookResponse, BookWithDetailsResponse,
    PaginatedResponse, CategoryInBookResponse, AuthorInBookResponse
)
from src.schemas.user import UserCreate, UserLogin, UserResponse, UserUpdate, Token, TokenData
from src.schemas.author import (
    AuthorCreate, AuthorUpdate, AuthorResponse, AuthorWithBooksResponse, BookInAuthorResponse
)
from src.schemas.category import (
    CategoryCreate, CategoryUpdate, CategoryResponse, CategoryWithBooksResponse,
    BookInCategoryResponse, BookCategoriesUpdate
)
from src.schemas.review import (
    ReviewCreate, ReviewUpdate, ReviewResponse, ReviewWithDetailsResponse,
    ReviewUserResponse, ReviewBookResponse
)

__all__ = [
    # Book schemas
    "BookCreate", "BookUpdate", "BookResponse", "BookWithDetailsResponse",
    "PaginatedResponse", "CategoryInBookResponse", "AuthorInBookResponse",
    # User schemas
    "UserCreate", "UserLogin", "UserResponse", "UserUpdate", "Token", "TokenData",
    # Author schemas
    "AuthorCreate", "AuthorUpdate", "AuthorResponse", "AuthorWithBooksResponse", "BookInAuthorResponse",
    # Category schemas
    "CategoryCreate", "CategoryUpdate", "CategoryResponse", "CategoryWithBooksResponse",
    "BookInCategoryResponse", "BookCategoriesUpdate",
    # Review schemas
    "ReviewCreate", "ReviewUpdate", "ReviewResponse", "ReviewWithDetailsResponse",
    "ReviewUserResponse", "ReviewBookResponse",
]
