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


