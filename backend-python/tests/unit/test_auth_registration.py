"""
Unit tests for Authentication Registration endpoints.
"""

from fastapi.testclient import TestClient

# Standard strong password for tests
STRONG_PASSWORD = "TestPassword123!"


def test_register_user(client):
    """Test user registration with valid data."""
    user_data = {
        "email": "newuser@example.com",
        "password": STRONG_PASSWORD,
        "role": "user"
    }
    response = client.post("/register", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["role"] == "user"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "hashed_password" not in data  # Password should not be in response


def test_register_forces_user_role(client):
    """Test that registration with 'admin' role still creates a 'user'"""
    admin_data = {
        "email": "admin@example.com",
        "password": STRONG_PASSWORD,
        "role": "admin"
    }
    response = client.post("/register", json=admin_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == admin_data["email"]
    # Note: Registration now forces all users to 'user' role
    assert data["role"] == "user"


def test_register_duplicate_email(client):
    """Test that registering with duplicate email returns 400."""
    user_data = {
        "email": "duplicate@example.com",
        "password": STRONG_PASSWORD,
        "role": "user"
    }
    # Register first time
    response = client.post("/register", json=user_data)
    assert response.status_code == 201
    
    # Try to register again with same email
    response = client.post("/register", json=user_data)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_register_weak_password(client):
    """Test that weak passwords are rejected."""
    user_data = {
        "email": "weak@example.com",
        "password": "short",  # Too short, no digits
        "role": "user"
    }
    response = client.post("/register", json=user_data)
    assert response.status_code == 422  # Validation error


def test_register_invalid_email(client):
    """Test that invalid email format is rejected."""
    user_data = {
        "email": "not-an-email",
        "password": STRONG_PASSWORD,
        "role": "user"
    }
    response = client.post("/register", json=user_data)
    assert response.status_code == 422  # Validation error


def test_registration_forces_user_role_security(client):
    """Test that registration always creates users with 'user' role (security fix)."""
    # Registration should always force role to 'user'
    response = client.post("/register", json={
        "email": "secureuser@test.com",
        "password": STRONG_PASSWORD
    })
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "user"  # Always 'user', never 'admin'
