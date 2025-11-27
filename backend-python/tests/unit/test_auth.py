"""
Unit tests for Authentication endpoints.
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient


def test_register_user(client):
    """Test user registration with valid data."""
    user_data = {
        "email": "newuser@example.com",
        "password": "testpassword123",
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


def test_register_admin(client):
    """Test admin registration."""
    admin_data = {
        "email": "admin@example.com",
        "password": "adminpassword123",
        "role": "admin"
    }
    response = client.post("/register", json=admin_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == admin_data["email"]
    assert data["role"] == "admin"


def test_register_duplicate_email(client):
    """Test that registering with duplicate email returns 400."""
    user_data = {
        "email": "duplicate@example.com",
        "password": "testpassword123",
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
        "password": "testpassword123",
        "role": "user"
    }
    response = client.post("/register", json=user_data)
    assert response.status_code == 422  # Validation error


def test_login_success(client):
    """Test successful login returns JWT token."""
    # First register a user
    register_data = {
        "email": "logintest@example.com",
        "password": "testpassword123",
        "role": "user"
    }
    client.post("/register", json=register_data)
    
    # Now login
    login_data = {
        "email": "logintest@example.com",
        "password": "testpassword123"
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
        "password": "testpassword123",
        "role": "user"
    }
    client.post("/register", json=register_data)
    
    # Try to login with wrong password
    login_data = {
        "email": "wrongpass@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/login", json=login_data)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_nonexistent_user(client):
    """Test login with non-existent email returns 401."""
    login_data = {
        "email": "doesnotexist@example.com",
        "password": "testpassword123"
    }
    response = client.post("/login", json=login_data)
    assert response.status_code == 401


def test_get_current_user_profile(client):
    """Test getting current user profile with valid token."""
    # Register and login
    register_data = {
        "email": "profile@example.com",
        "password": "testpassword123",
        "role": "user"
    }
    client.post("/register", json=register_data)
    
    login_response = client.post("/login", json={
        "email": "profile@example.com",
        "password": "testpassword123"
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


def test_update_user_profile(client):
    """Test updating user profile."""
    # Register and login
    register_data = {
        "email": "updateme@example.com",
        "password": "testpassword123",
        "role": "user"
    }
    client.post("/register", json=register_data)
    
    login_response = client.post("/login", json={
        "email": "updateme@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    # Update profile
    update_data = {
        "email": "newemail@example.com"
    }
    response = client.put(
        "/me",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newemail@example.com"


def test_create_book_authenticated(client):
    """Test creating a book with authentication."""
    # Register and login
    register_data = {
        "email": "bookauthor@example.com",
        "password": "testpassword123",
        "role": "user"
    }
    client.post("/register", json=register_data)
    
    login_response = client.post("/login", json={
        "email": "bookauthor@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    # Create book
    book_data = {
        "title": "Authenticated Book",
        "author": "Auth Author",
        "isbn": "9781234567890",
        "published_date": "2023-06-15",
        "description": "A book created by authenticated user"
    }
    response = client.post(
        "/books",
        json=book_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == book_data["title"]
    assert "created_by" in data
    assert data["created_by"] is not None


def test_create_book_unauthenticated(client):
    """Test creating a book without authentication returns 403."""
    book_data = {
        "title": "Unauthorized Book",
        "author": "No Auth",
        "isbn": "9780987654321",
        "published_date": "2023-06-15"
    }
    response = client.post("/books", json=book_data)
    assert response.status_code == 403


def test_delete_book_as_admin(client):
    """Test that admin can delete books."""
    # Register admin and user
    admin_data = {
        "email": "adminuser@example.com",
        "password": "adminpassword123",
        "role": "admin"
    }
    user_data = {
        "email": "regularuser@example.com",
        "password": "testpassword123",
        "role": "user"
    }
    client.post("/register", json=admin_data)
    client.post("/register", json=user_data)
    
    # Login as user and create book
    user_login = client.post("/login", json={
        "email": "regularuser@example.com",
        "password": "testpassword123"
    })
    user_token = user_login.json()["access_token"]
    
    book_data = {
        "title": "Book to Delete",
        "author": "Delete Author",
        "isbn": "9781111111111",
        "published_date": "2023-06-15"
    }
    create_response = client.post(
        "/books",
        json=book_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    book_id = create_response.json()["id"]
    
    # Login as admin and delete book
    admin_login = client.post("/login", json={
        "email": "adminuser@example.com",
        "password": "adminpassword123"
    })
    admin_token = admin_login.json()["access_token"]
    
    response = client.delete(
        f"/books/{book_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]


def test_delete_book_as_non_admin(client):
    """Test that regular user cannot delete books."""
    # Register user
    user_data = {
        "email": "nonadmin@example.com",
        "password": "testpassword123",
        "role": "user"
    }
    client.post("/register", json=user_data)
    
    # Login and create book
    login_response = client.post("/login", json={
        "email": "nonadmin@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    book_data = {
        "title": "Cannot Delete",
        "author": "No Delete Author",
        "isbn": "9782222222222",
        "published_date": "2023-06-15"
    }
    create_response = client.post(
        "/books",
        json=book_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    book_id = create_response.json()["id"]
    
    # Try to delete as regular user
    response = client.delete(
        f"/books/{book_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()


# =============================================================================
# User Management Tests (Admin-Only Role Promotion/Demotion)
# =============================================================================

def test_promote_user_to_admin(client):
    """Test that admin can promote user to admin role."""
    from tests.conftest import get_auth_headers

    # Create admin user
    admin_headers = get_auth_headers(client, "admin@test.com", "admin123", "admin")

    # Register a regular user
    response = client.post("/register", json={
        "email": "user@test.com",
        "password": "testpass123"
    })
    assert response.status_code == 201
    user_id = response.json()["id"]
    assert response.json()["role"] == "user"

    # Promote user to admin
    response = client.patch(
        f"/users/{user_id}/role",
        json={"role": "admin"},
        headers=admin_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["role"] == "admin"
    assert data["email"] == "user@test.com"


def test_demote_admin_to_user(client):
    """Test that admin can demote another admin to user role."""
    from tests.conftest import get_auth_headers, create_admin_user

    # Create two admin users
    admin1_headers = get_auth_headers(client, "admin1@test.com", "admin123", "admin")
    admin2_data = create_admin_user(client, "admin2@test.com", "admin123")

    # Demote admin2 to user
    response = client.patch(
        f"/users/{admin2_data['id']}/role",
        json={"role": "user"},
        headers=admin1_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == admin2_data["id"]
    assert data["role"] == "user"


def test_cannot_demote_last_admin(client):
    """Test that system prevents demoting the last admin."""
    from tests.conftest import get_auth_headers, create_admin_user

    # Create single admin user
    admin_headers = get_auth_headers(client, "admin@test.com", "admin123", "admin")
    admin_data = create_admin_user(client, "admin@test.com", "admin123")

    # Try to demote the only admin
    response = client.patch(
        f"/users/{admin_data['id']}/role",
        json={"role": "user"},
        headers=admin_headers
    )
    assert response.status_code == 400
    assert "last admin" in response.json()["detail"].lower()


def test_non_admin_cannot_promote_users(client):
    """Test that regular users cannot promote other users."""
    from tests.conftest import get_auth_headers

    # Create regular user
    user_headers = get_auth_headers(client, "user@test.com", "testpass123", "user")

    # Register another user to promote
    response = client.post("/register", json={
        "email": "user2@test.com",
        "password": "testpass123"
    })
    user2_id = response.json()["id"]

    # Try to promote as regular user (should fail)
    response = client.patch(
        f"/users/{user2_id}/role",
        json={"role": "admin"},
        headers=user_headers
    )
    assert response.status_code == 403
    assert "admin" in response.json()["detail"].lower()


def test_promote_nonexistent_user(client):
    """Test that promoting non-existent user returns 404."""
    from tests.conftest import get_auth_headers

    admin_headers = get_auth_headers(client, "admin@test.com", "admin123", "admin")

    response = client.patch(
        "/users/99999/role",
        json={"role": "admin"},
        headers=admin_headers
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_promote_without_authentication(client):
    """Test that unauthenticated requests are rejected."""
    # Register a user
    response = client.post("/register", json={
        "email": "user@test.com",
        "password": "testpass123"
    })
    user_id = response.json()["id"]

    # Try to promote without auth
    response = client.patch(
        f"/users/{user_id}/role",
        json={"role": "admin"}
    )
    assert response.status_code == 403


def test_list_all_users_as_admin(client):
    """Test that admin can list all users."""
    from tests.conftest import get_auth_headers

    # Create admin
    admin_headers = get_auth_headers(client, "admin@test.com", "admin123", "admin")

    # Create some regular users
    client.post("/register", json={"email": "user1@test.com", "password": "pass123"})
    client.post("/register", json={"email": "user2@test.com", "password": "pass123"})

    # List all users
    response = client.get("/users", headers=admin_headers)
    assert response.status_code == 200
    users = response.json()
    assert len(users) >= 3  # admin + 2 regular users
    assert any(u["email"] == "admin@test.com" for u in users)
    assert any(u["email"] == "user1@test.com" for u in users)


def test_list_users_as_regular_user_fails(client):
    """Test that regular users cannot list all users."""
    from tests.conftest import get_auth_headers

    user_headers = get_auth_headers(client, "user@test.com", "testpass123", "user")

    response = client.get("/users", headers=user_headers)
    assert response.status_code == 403


def test_get_user_by_id_as_admin(client):
    """Test that admin can get specific user by ID."""
    from tests.conftest import get_auth_headers

    admin_headers = get_auth_headers(client, "admin@test.com", "admin123", "admin")

    # Create a user
    response = client.post("/register", json={
        "email": "user@test.com",
        "password": "testpass123"
    })
    user_id = response.json()["id"]

    # Get user by ID
    response = client.get(f"/users/{user_id}", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["email"] == "user@test.com"
    assert data["role"] == "user"


def test_get_nonexistent_user_returns_404(client):
    """Test that getting non-existent user returns 404."""
    from tests.conftest import get_auth_headers

    admin_headers = get_auth_headers(client, "admin@test.com", "admin123", "admin")

    response = client.get("/users/99999", headers=admin_headers)
    assert response.status_code == 404


def test_registration_forces_user_role(client):
    """Test that registration always creates users with 'user' role (security fix)."""
    # Registration should always force role to 'user'
    response = client.post("/register", json={
        "email": "secureuser@test.com",
        "password": "testpass123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "user"  # Always 'user', never 'admin'


