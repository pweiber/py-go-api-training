"""
Unit tests for Authentication endpoints.
"""
import pytest
from datetime import datetime
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
    assert "Current password required" in response.json()["detail"]


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
    assert "Current password is incorrect" in response.json()["detail"]


def test_create_book_authenticated(client):
    """Test creating a book with authentication."""
    # Register and login
    register_data = {
        "email": "bookauthor@example.com",
        "password": STRONG_PASSWORD,
        "role": "user"
    }
    client.post("/register", json=register_data)
    
    login_response = client.post("/login", json={
        "email": "bookauthor@example.com",
        "password": STRONG_PASSWORD
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
    from tests.conftest import create_admin_user

    # Register user
    user_data = {
        "email": "regularuser@example.com",
        "password": STRONG_PASSWORD,
        "role": "user"
    }
    client.post("/register", json=user_data)
    
    # Create admin
    create_admin_user(client, "adminuser@example.com", STRONG_PASSWORD)
    
    # Login as user and create book
    user_login = client.post("/login", json={
        "email": "regularuser@example.com",
        "password": STRONG_PASSWORD
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
        "password": STRONG_PASSWORD
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
        "password": STRONG_PASSWORD,
        "role": "user"
    }
    client.post("/register", json=user_data)
    
    # Login and create book
    login_response = client.post("/login", json={
        "email": "nonadmin@example.com",
        "password": STRONG_PASSWORD
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
    admin_headers = get_auth_headers(client, "admin@test.com", STRONG_PASSWORD, "admin")

    # Register a regular user
    response = client.post("/register", json={
        "email": "user@test.com",
        "password": STRONG_PASSWORD
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
    admin1_headers = get_auth_headers(client, "admin1@test.com", STRONG_PASSWORD, "admin")
    admin2_data = create_admin_user(client, "admin2@test.com", STRONG_PASSWORD)

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

    # Create single admin user using create_admin_user only (no duplicate registration)
    admin_data = create_admin_user(client, "admin@test.com", STRONG_PASSWORD)
    
    # Login as admin
    login_response = client.post("/login", json={
        "email": "admin@test.com",
        "password": STRONG_PASSWORD
    })
    admin_token = login_response.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

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
    user_headers = get_auth_headers(client, "user@test.com", STRONG_PASSWORD, "user")

    # Register another user to promote
    response = client.post("/register", json={
        "email": "user2@test.com",
        "password": STRONG_PASSWORD
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

    admin_headers = get_auth_headers(client, "admin@test.com", STRONG_PASSWORD, "admin")

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
        "password": STRONG_PASSWORD
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
    admin_headers = get_auth_headers(client, "admin@test.com", STRONG_PASSWORD, "admin")

    # Create some regular users
    client.post("/register", json={"email": "user1@test.com", "password": STRONG_PASSWORD})
    client.post("/register", json={"email": "user2@test.com", "password": STRONG_PASSWORD})

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

    user_headers = get_auth_headers(client, "user@test.com", STRONG_PASSWORD, "user")

    response = client.get("/users", headers=user_headers)
    assert response.status_code == 403


def test_get_user_by_id_as_admin(client):
    """Test that admin can get specific user by ID."""
    from tests.conftest import get_auth_headers

    admin_headers = get_auth_headers(client, "admin@test.com", STRONG_PASSWORD, "admin")

    # Create a user
    response = client.post("/register", json={
        "email": "user@test.com",
        "password": STRONG_PASSWORD
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

    admin_headers = get_auth_headers(client, "admin@test.com", STRONG_PASSWORD, "admin")

    response = client.get("/users/99999", headers=admin_headers)
    assert response.status_code == 404


def test_registration_forces_user_role(client):
    """Test that registration always creates users with 'user' role (security fix)."""
    # Registration should always force role to 'user'
    response = client.post("/register", json={
        "email": "secureuser@test.com",
        "password": STRONG_PASSWORD
    })
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "user"  # Always 'user', never 'admin'


# =============================================================================
# New Security Tests
# =============================================================================

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


def test_update_book_authorization(client):
    """Test that non-owner cannot update book."""
    # Register two users
    user1_data = {
        "email": "user1@example.com",
        "password": STRONG_PASSWORD
    }
    user2_data = {
        "email": "user2@example.com",
        "password": STRONG_PASSWORD
    }
    client.post("/register", json=user1_data)
    client.post("/register", json=user2_data)
    
    # Login as user1 and create book
    login1 = client.post("/login", json={"email": "user1@example.com", "password": STRONG_PASSWORD})
    token1 = login1.json()["access_token"]
    
    book_data = {
        "title": "User1's Book",
        "author": "Author",
        "isbn": "9781234567890",
        "published_date": "2023-06-15"
    }
    create_response = client.post("/books", json=book_data, headers={"Authorization": f"Bearer {token1}"})
    book_id = create_response.json()["id"]
    
    # Login as user2 and try to update user1's book
    login2 = client.post("/login", json={"email": "user2@example.com", "password": STRONG_PASSWORD})
    token2 = login2.json()["access_token"]
    
    update_response = client.put(
        f"/books/{book_id}",
        json={"title": "Hijacked Book"},
        headers={"Authorization": f"Bearer {token2}"}
    )
    assert update_response.status_code == 403
    assert "your own books" in update_response.json()["detail"].lower()


def test_admin_can_update_any_book(client):
    """Test that admin can update any book."""
    from tests.conftest import create_admin_user
    
    # Register regular user and create book
    user_data = {
        "email": "user@example.com",
        "password": STRONG_PASSWORD
    }
    client.post("/register", json=user_data)
    
    login = client.post("/login", json={"email": "user@example.com", "password": STRONG_PASSWORD})
    user_token = login.json()["access_token"]
    
    book_data = {
        "title": "User's Book",
        "author": "Author",
        "isbn": "9781234567890",
        "published_date": "2023-06-15"
    }
    create_response = client.post("/books", json=book_data, headers={"Authorization": f"Bearer {user_token}"})
    book_id = create_response.json()["id"]
    
    # Create admin and update the book
    create_admin_user(client, "admin@example.com", STRONG_PASSWORD)
    admin_login = client.post("/login", json={"email": "admin@example.com", "password": STRONG_PASSWORD})
    admin_token = admin_login.json()["access_token"]
    
    update_response = client.put(
        f"/books/{book_id}",
        json={"title": "Admin Updated Book"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Admin Updated Book"


def test_owner_can_update_own_book(client):
    """Test that owner can update their own book."""
    # Register user and create book
    user_data = {
        "email": "owner@example.com",
        "password": STRONG_PASSWORD
    }
    client.post("/register", json=user_data)
    
    login = client.post("/login", json={"email": "owner@example.com", "password": STRONG_PASSWORD})
    token = login.json()["access_token"]
    
    book_data = {
        "title": "My Book",
        "author": "Author",
        "isbn": "9781234567890",
        "published_date": "2023-06-15"
    }
    create_response = client.post("/books", json=book_data, headers={"Authorization": f"Bearer {token}"})
    book_id = create_response.json()["id"]
    
    # Owner updates their own book
    update_response = client.put(
        f"/books/{book_id}",
        json={"title": "Updated My Book"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Updated My Book"


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

