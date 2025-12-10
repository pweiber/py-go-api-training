"""
Unit tests for Authentication Login endpoints.
"""

from fastapi.testclient import TestClient

# Standard strong password for tests
STRONG_PASSWORD = "TestPassword123!"


def test_login_success(client):
    """Test successful login returns JWT token."""
    # First register a user
    register_data = {
        "email": "logintest@example.com",
        "password": STRONG_PASSWORD,
        "role": "user"
    }
    client.post("/register", json=register_data)
    
    # Now login
    login_data = {
        "email": "logintest@example.com",
        "password": STRONG_PASSWORD
    }
    response = client.post("/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0


def test_login_wrong_password(client):
    """Test login with wrong password returns 401."""
    # First register a user
    register_data = {
        "email": "wrongpass@example.com",
        "password": STRONG_PASSWORD,
        "role": "user"
    }
    client.post("/register", json=register_data)
    
    # Try to login with wrong password
    login_data = {
        "email": "wrongpass@example.com",
        "password": "WrongPassword123!"
    }
    response = client.post("/login", json=login_data)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_nonexistent_user(client):
    """Test login with non-existent email returns 401."""
    login_data = {
        "email": "doesnotexist@example.com",
        "password": STRONG_PASSWORD
    }
    response = client.post("/login", json=login_data)
    assert response.status_code == 401
