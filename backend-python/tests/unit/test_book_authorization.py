"""
Unit tests for Book Authorization endpoints.
"""

from fastapi.testclient import TestClient

# Standard strong password for tests
STRONG_PASSWORD = "TestPassword123!"


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
        "/api/v1/books",
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
    response = client.post("/api/v1/books", json=book_data)
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
        "/api/v1/books",
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
        f"/api/v1/books/{book_id}",
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
        "/api/v1/books",
        json=book_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    book_id = create_response.json()["id"]
    
    # Try to delete as regular user
    response = client.delete(
        f"/api/v1/books/{book_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()


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
    create_response = client.post("/api/v1/books", json=book_data, headers={"Authorization": f"Bearer {token1}"})
    book_id = create_response.json()["id"]
    
    # Login as user2 and try to update user1's book
    login2 = client.post("/login", json={"email": "user2@example.com", "password": STRONG_PASSWORD})
    token2 = login2.json()["access_token"]
    
    update_response = client.put(
        f"/api/v1/books/{book_id}",
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
    create_response = client.post("/api/v1/books", json=book_data, headers={"Authorization": f"Bearer {user_token}"})
    book_id = create_response.json()["id"]
    
    # Create admin and update the book
    create_admin_user(client, "admin@example.com", STRONG_PASSWORD)
    admin_login = client.post("/login", json={"email": "admin@example.com", "password": STRONG_PASSWORD})
    admin_token = admin_login.json()["access_token"]
    
    update_response = client.put(
        f"/api/v1/books/{book_id}",
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
    create_response = client.post("/api/v1/books", json=book_data, headers={"Authorization": f"Bearer {token}"})
    book_id = create_response.json()["id"]
    
    # Owner updates their own book
    update_response = client.put(
        f"/api/v1/books/{book_id}",
        json={"title": "Updated My Book"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Updated My Book"
