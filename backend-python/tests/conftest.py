"""
Test configuration and fixtures for pytest.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.core.database import Base, get_db
from src.models.user import User

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
    """Sample book data for testing."""
    return {
        "title": "Test Book",
        "author": "Test Author",
        "isbn": "978-0123456789",
        "published_date": "2023-01-15",
        "description": "A test book"
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
    response = client.post("/register", json={
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


def get_auth_headers(client: TestClient, email: str, password: str, role: str = "user") -> dict:
    """
    Helper to register/create user and return authentication headers.

    Args:
        client: FastAPI test client
        email: User email
        password: User password
        role: User role - 'user' or 'admin' (default: 'user')

    Returns:
        dict: Headers with JWT Bearer token for authenticated requests

    Example:
        headers = get_auth_headers(client, "user@test.com", "Pass123!", "admin")
        response = client.get("/users", headers=headers)
    """
    if role == "admin":
        # Create admin user using helper
        create_admin_user(client, email, password)
    else:
        # Register regular user
        response = client.post("/register", json={
            "email": email,
            "password": password
        })
        assert response.status_code == 201

    # Login to get token
    login_response = client.post("/login", json={
        "email": email,
        "password": password
    })
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}
