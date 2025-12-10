"""
Unit tests for User Profile endpoints.
"""

from fastapi.testclient import TestClient

# Standard strong password for tests
STRONG_PASSWORD = "TestPassword123!"


def test_get_current_user_profile(client):
    """Test getting current user profile with valid token."""
    # Register and login
    register_data = {
        "email": "profile@example.com",
        "password": STRONG_PASSWORD,
        "role": "user"
    }
    client.post("/register", json=register_data)
    
    login_response = client.post("/login", json={
        "email": "profile@example.com",
        "password": STRONG_PASSWORD
    })
    token = login_response.json()["access_token"]
    
    # Get profile
    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "profile@example.com"
    assert data["role"] == "user"
    assert "hashed_password" not in data


def test_get_current_user_no_token(client):
    """Test getting profile without token returns 403."""
    response = client.get("/me")
    assert response.status_code == 403


def test_get_current_user_invalid_token(client):
    """Test getting profile with invalid token returns 401."""
    response = client.get("/me", headers={"Authorization": "Bearer invalid-token"})
    assert response.status_code == 401


def test_update_user_profile_email_change_requires_password(client):
    """Test updating email requires current password."""
    # Register and login
    register_data = {
        "email": "updateme@example.com",
        "password": STRONG_PASSWORD,
        "role": "user"
    }
    client.post("/register", json=register_data)
    
    login_response = client.post("/login", json={
        "email": "updateme@example.com",
        "password": STRONG_PASSWORD
    })
    token = login_response.json()["access_token"]
    
    # Try to update email without password - should fail
    update_data = {
        "email": "newemail@example.com"
    }
    response = client.put(
        "/me",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert "Incorrect or missing current password" in response.json()["detail"]


def test_update_user_profile_email_with_password(client):
    """Test updating email with correct password succeeds."""
    # Register and login
    register_data = {
        "email": "updatewithpass@example.com",
        "password": STRONG_PASSWORD,
        "role": "user"
    }
    client.post("/register", json=register_data)
    
    login_response = client.post("/login", json={
        "email": "updatewithpass@example.com",
        "password": STRONG_PASSWORD
    })
    token = login_response.json()["access_token"]
    
    # Update email with correct password
    update_data = {
        "email": "newemail@example.com",
        "current_password": STRONG_PASSWORD
    }
    response = client.put(
        "/me",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newemail@example.com"


def test_update_user_profile_email_with_wrong_password(client):
    """Test updating email with wrong password fails."""
    # Register and login
    register_data = {
        "email": "updatewrongpass@example.com",
        "password": STRONG_PASSWORD,
        "role": "user"
    }
    client.post("/register", json=register_data)
    
    login_response = client.post("/login", json={
        "email": "updatewrongpass@example.com",
        "password": STRONG_PASSWORD
    })
    token = login_response.json()["access_token"]
    
    # Try to update email with wrong password
    update_data = {
        "email": "newemail@example.com",
        "current_password": "WrongPassword123!"
    }
    response = client.put(
        "/me",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert "Incorrect or missing current password" in response.json()["detail"]


def test_update_password_requires_current_password(client):
    """Test updating password requires current password verification."""
    # Register and login
    register_data = {
        "email": "passcheck@example.com",
        "password": STRONG_PASSWORD,
        "role": "user"
    }
    client.post("/register", json=register_data)
    
    login_response = client.post("/login", json={
        "email": "passcheck@example.com",
        "password": STRONG_PASSWORD
    })
    token = login_response.json()["access_token"]
    
    # Try to update password without current_password
    response = client.put(
        "/me",
        json={"password": "NewStrongPassword123!"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert "Incorrect or missing current password" in response.json()["detail"]


def test_update_password_with_wrong_current_password(client):
    """Test updating password with wrong current password fails."""
    # Register and login
    register_data = {
        "email": "wrongpasscheck@example.com",
        "password": STRONG_PASSWORD,
        "role": "user"
    }
    client.post("/register", json=register_data)
    
    login_response = client.post("/login", json={
        "email": "wrongpasscheck@example.com",
        "password": STRONG_PASSWORD
    })
    token = login_response.json()["access_token"]
    
    # Try to update password with wrong current_password
    response = client.put(
        "/me",
        json={
            "password": "NewStrongPassword123!",
            "current_password": "WrongPassword123!"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert "Incorrect or missing current password" in response.json()["detail"]


def test_update_password_success(client):
    """Test updating password with correct current password succeeds."""
    # Register and login
    register_data = {
        "email": "goodpasscheck@example.com",
        "password": STRONG_PASSWORD,
        "role": "user"
    }
    client.post("/register", json=register_data)
    
    login_response = client.post("/login", json={
        "email": "goodpasscheck@example.com",
        "password": STRONG_PASSWORD
    })
    token = login_response.json()["access_token"]
    
    # Update password successfully
    new_password = "NewStrongPassword123!"
    response = client.put(
        "/me",
        json={
            "password": new_password,
            "current_password": STRONG_PASSWORD
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    # Verify new password works
    login_response = client.post("/login", json={
        "email": "goodpasscheck@example.com",
        "password": new_password
    })
    assert login_response.status_code == 200
