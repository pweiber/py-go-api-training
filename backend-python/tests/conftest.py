"""
Test configuration and fixtures for pytest.
"""
import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.core.database import Base, get_db
from src.models.user import User
from src.core.rate_limit import limiter

# Disable rate limiting for tests
limiter.enabled = False

# Common constants
STRONG_PASSWORD = "StrongP@ssw0rd!"

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override the get_db dependency to use test database."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client():
    """
    Create a fresh test database and client for each test.
    """
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Override the dependency
    app.dependency_overrides[get_db] = override_get_db

    # Create test client
    with TestClient(app) as test_client:
        yield test_client

    # Clean up - drop all tables after each test
    Base.metadata.drop_all(bind=engine)

    # Clear dependency overrides
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "role": "user"
    }


@pytest.fixture
def sample_book_data():
    """Sample book data for testing (NEW SCHEMA with author_ids and category_ids)."""
    return {
        "title": "Test Book",
        "isbn": "9780123456789",
        "published_date": "2023-01-15",
        "description": "A test book",
        "author_ids": [],
        "category_ids": []
    }


def create_admin_user(client: TestClient, email: str, password: str) -> dict:
    """
    Helper to create an admin user by registering and directly promoting in database.

    Args:
        client: FastAPI test client
        email: Admin email
        password: Admin password

    Returns:
        dict: User data with id, email, role
    """
    # Register the user
    response = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password
    })
    assert response.status_code == 201
    user_data = response.json()

    # Directly promote in database (bypasses API security)
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.id == user_data["id"]).first()
        if user:
            user.role = "admin"
            db.commit()
            db.refresh(user)
            return {
                "id": user.id,
                "email": user.email,
                "role": user.role
            }
    finally:
        db.close()

    return user_data


def get_auth_headers(client, email: str, password: str, is_admin: bool = False, role: str = None) -> dict:
    """
    Helper to register a user and return authentication headers.

    Args:
        client: FastAPI test client
        email: User email
        password: User password
        is_admin: Whether to create an admin user (default: False)
        role: Role name ("admin" or "user") - alternative to is_admin parameter

    Returns:
        dict: Authorization headers with Bearer token
    """
    # Support both is_admin and role parameters for backward compatibility
    if role is not None:
        is_admin = (role == "admin")

    # Register user
    register_data = {
        "email": email,
        "password": password
    }

    client.post("/api/v1/auth/register", json=register_data)

    # If admin is needed, promote the user in database
    if is_admin:
        db = TestingSessionLocal()
        try:
            user = db.query(User).filter(User.email == email).first()
            if user:
                user.role = "admin"
                db.commit()
        finally:
            db.close()

    # Login to get token
    login_data = {
        "email": email,
        "password": password
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def db_session():
    """Provide a database session for tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_test_author(client: TestClient, name: str = "Test Author", bio: str = None,
                       birth_date: str = None, nationality: str = None,
                       admin_headers: dict = None) -> dict:
    """
    Helper to create a test author.

    Args:
        client: FastAPI test client
        name: Author name
        bio: Author biography
        birth_date: Birth date (YYYY-MM-DD format)
        nationality: Author nationality
        admin_headers: Admin authentication headers (will create if not provided)

    Returns:
        dict: Created author data with id
    """
    if admin_headers is None:
        admin_headers = get_auth_headers(client, f"admin_{name.replace(' ', '_').lower()}@test.com", STRONG_PASSWORD, is_admin=True)

    author_data = {"name": name}
    if bio:
        author_data["bio"] = bio
    if birth_date:
        author_data["birth_date"] = birth_date
    if nationality:
        author_data["nationality"] = nationality

    response = client.post("/api/v1/authors", json=author_data, headers=admin_headers)
    assert response.status_code == 201, f"Failed to create author: {response.json()}"
    return response.json()


def create_test_category(client: TestClient, name: str = "Test Category",
                        description: str = None, admin_headers: dict = None) -> dict:
    """
    Helper to create a test category.

    Args:
        client: FastAPI test client
        name: Category name
        description: Category description
        admin_headers: Admin authentication headers (will create if not provided)

    Returns:
        dict: Created category data with id
    """
    if admin_headers is None:
        admin_headers = get_auth_headers(client, f"admin_{name.replace(' ', '_').lower()}@test.com", STRONG_PASSWORD, is_admin=True)

    category_data = {"name": name}
    if description:
        category_data["description"] = description

    response = client.post("/api/v1/categories", json=category_data, headers=admin_headers)
    assert response.status_code == 201, f"Failed to create category: {response.json()}"
    return response.json()


def create_test_book(client: TestClient, title: str = "Test Book", isbn: str = "9781234567890",
                    published_date: str = "2023-01-15", description: str = "Test description",
                    author_ids: list = None, category_ids: list = None,
                    admin_headers: dict = None) -> dict:
    """
    Helper to create a test book (requires admin).

    Args:
        client: FastAPI test client
        title: Book title
        isbn: Book ISBN (will be normalized)
        published_date: Publication date (YYYY-MM-DD format)
        description: Book description
        author_ids: List of author IDs (will create default author if None)
        category_ids: List of category IDs (empty list if None)
        admin_headers: Admin authentication headers (will create if not provided)

    Returns:
        dict: Created book data with id
    """
    if admin_headers is None:
        admin_headers = get_auth_headers(client, "admin_book_creator@test.com", STRONG_PASSWORD, is_admin=True)

    # If no author_ids provided, create a default author
    if author_ids is None:
        default_author = create_test_author(client, "Default Author", admin_headers=admin_headers)
        author_ids = [default_author["id"]]

    if category_ids is None:
        category_ids = []

    book_data = {
        "title": title,
        "isbn": isbn,
        "published_date": published_date,
        "description": description,
        "author_ids": author_ids,
        "category_ids": category_ids
    }

    response = client.post("/api/v1/books", json=book_data, headers=admin_headers)
    assert response.status_code == 201, f"Failed to create book: {response.json()}"
    return response.json()


@pytest.fixture
def sample_review(client, db_session):
    """Create a sample review for testing."""
    from src.models.review import Review

    # Create admin and author
    admin_headers = get_auth_headers(client, "admin_review@test.com", STRONG_PASSWORD, is_admin=True)
    author = create_test_author(client, "Sample Author", admin_headers=admin_headers)

    # Create a book
    book = create_test_book(
        client,
        title="Sample Book",
        isbn="9781234567890",
        published_date="2023-01-01",
        author_ids=[author["id"]],
        admin_headers=admin_headers
    )
    book_id = book["id"]

    # Create a reviewer (different user)
    reviewer_headers = get_auth_headers(client, "reviewer@test.com", STRONG_PASSWORD)

    # Create a review
    review_response = client.post(f"/api/v1/books/{book_id}/reviews", headers=reviewer_headers, json={
        "rating": 5,
        "comment": "Great book!"
    })

    review_id = review_response.json()["id"]

    # Fetch the review from database
    review = db_session.query(Review).filter(Review.id == review_id).first()
    return review

