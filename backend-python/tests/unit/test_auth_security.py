"""
Unit tests for Auth Security (tokens, passwords) endpoints.
"""

from fastapi.testclient import TestClient

# Standard strong password for tests
STRONG_PASSWORD = "TestPassword123!"


def test_token_without_user_id_returns_401(client):
    """Test that token without user_id returns 401."""
    from jose import jwt
    from src.core.config import settings
    from datetime import datetime, timedelta, timezone
    
    # Create a token without user_id
    token_data = {
        "sub": "test@example.com",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30)
    }
    invalid_token = jwt.encode(token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    # Try to access protected endpoint
    response = client.get("/me", headers={"Authorization": f"Bearer {invalid_token}"})
    assert response.status_code == 401


def test_email_normalized_to_lowercase(client):
    """Test that emails are normalized to lowercase."""
    # Register with uppercase email
    response = client.post("/register", json={
        "email": "UPPERCASE@EXAMPLE.COM",
        "password": STRONG_PASSWORD
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "uppercase@example.com"
    
    # Login with different case - should work
    login_response = client.post("/login", json={
        "email": "Uppercase@Example.COM",
        "password": STRONG_PASSWORD
    })
    assert login_response.status_code == 200


def test_password_strength_requirements(client):
    """Test that password validation enforces all requirements."""
    # Missing lowercase
    response = client.post("/register", json={"email": "test1@example.com", "password": "ALLUPPERCASE123!"})
    assert response.status_code == 422
    
    # Missing uppercase
    response = client.post("/register", json={"email": "test2@example.com", "password": "alllowercase123!"})
    assert response.status_code == 422
    
    # Missing digit
    response = client.post("/register", json={"email": "test3@example.com", "password": "NoDigitsHere!"})
    assert response.status_code == 422
    
    # Missing special character
    response = client.post("/register", json={"email": "test4@example.com", "password": "NoSpecialChar123"})
    assert response.status_code == 422
    
    # Too short
    response = client.post("/register", json={"email": "test5@example.com", "password": "Abc1!"})
    assert response.status_code == 422
    
    # Valid password
    response = client.post("/register", json={"email": "test6@example.com", "password": STRONG_PASSWORD})
    assert response.status_code == 201
