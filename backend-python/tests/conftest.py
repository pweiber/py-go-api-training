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


def create_admin_user(client: TestClient, email: str = "admin@test.com", password: str = "admin123") -> dict:
    """
    Helper function to create an admin user for testing.

    Since normal registration now forces UserRole.USER, this function:
    1. Registers a regular user
    2. Directly updates their role in the database to ADMIN

    Args:
        client: TestClient instance
        email: Admin email
        password: Admin password

    Returns:
        User data dictionary with id, email, role, etc.
    """
    from src.models.user import User, UserRole

    # Register as regular user
    response = client.post("/register", json={
        "email": email,
        "password": password
    })
    assert response.status_code == 201
    user_data = response.json()

    # Directly update role in database (bypass API for testing)
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.id == user_data["id"]).first()
        user.role = UserRole.ADMIN
        db.commit()
        db.refresh(user)
        user_data["role"] = user.role.value
    finally:
        db.close()

    return user_data


def get_auth_headers(client: TestClient, email: str = "user@test.com", password: str = "testpass123", role: str = "user") -> dict:
    """
    Helper function to get authentication headers for testing.

    Args:
        client: TestClient instance
        email: User email
        password: User password
        role: User role ('user' or 'admin')

    Returns:
        Headers dictionary with Authorization Bearer token
    """
    # If admin role requested, create admin user
    if role == "admin":
        create_admin_user(client, email, password)
    else:
        # Register regular user
        client.post("/register", json={
            "email": email,
            "password": password
        })

    # Login to get token
    response = client.post("/login", json={
        "email": email,
        "password": password
    })
    assert response.status_code == 200
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


