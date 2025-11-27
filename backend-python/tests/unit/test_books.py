"""
Unit tests for Book CRUD endpoints.
"""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Standard strong password for tests
STRONG_PASSWORD = "TestPassword123!"


def test_health_check(client):
    """Test the root endpoint returns correct message."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Book Store API"}

def test_create_book_duplicate_isbn(client):
    """Test creating a book with duplicate ISBN returns 400."""
    # Register and login to get token
    client.post("/register", json={
        "email": "booktest@example.com",
        "password": STRONG_PASSWORD,
        "role": "user"
    })
    login_response = client.post("/login", json={
        "email": "booktest@example.com",
        "password": STRONG_PASSWORD
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    book_data = {
        "title": "Test Book",
        "author": "Test Author",
        "isbn": "978-1234567890",
        "published_date": "2023-01-15",
        "description": "Test description"
    }
    # Create first book
    response = client.post("/books", json=book_data, headers=headers)
    assert response.status_code == 201
    
    # Try to create duplicate
    response = client.post("/books", json=book_data, headers=headers)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_get_all_books(client):
    """Test getting all books."""
    # Register and login to get token
    client.post("/register", json={
        "email": "getbooks@example.com",
        "password": STRONG_PASSWORD,
        "role": "user"
    })
    login_response = client.post("/login", json={
        "email": "getbooks@example.com",
        "password": STRONG_PASSWORD
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create a test book first
    book_data = {
        "title": "Test Book",
        "author": "Test Author",
        "isbn": "978-1111111111",
        "published_date": "2023-01-15",
        "description": "Test description"
    }
    client.post("/books", json=book_data, headers=headers)

    response = client.get("/books", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_book_by_id(client):
    """Test getting a specific book by ID."""
    # Register and login to get token
    client.post("/register", json={
        "email": "getbyid@example.com",
        "password": STRONG_PASSWORD,
        "role": "user"
    })
    login_response = client.post("/login", json={
        "email": "getbyid@example.com",
        "password": STRONG_PASSWORD
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create a test book
    book_data = {
        "title": "Specific Book",
        "author": "Specific Author",
        "isbn": "978-2222222222",
        "published_date": "2023-01-15",
        "description": "Specific description"
    }
    create_response = client.post("/books", json=book_data, headers=headers)
    book_id = create_response.json()["id"]
    
    response = client.get(f"/books/{book_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == book_id
    assert data["title"] == book_data["title"]


def test_get_book_by_id_not_found(client):
    """Test getting a non-existent book returns 404."""
    response = client.get("/books/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_update_book(client):
    """Test updating a book (by owner)."""
    # Register and login to get token
    client.post("/register", json={
        "email": "updatebook@example.com",
        "password": STRONG_PASSWORD,
        "role": "user"
    })
    login_response = client.post("/login", json={
        "email": "updatebook@example.com",
        "password": STRONG_PASSWORD
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create a test book
    book_data = {
        "title": "Original Title",
        "author": "Original Author",
        "isbn": "978-3333333333",
        "published_date": "2023-01-15",
        "description": "Original description"
    }
    create_response = client.post("/books", json=book_data, headers=headers)
    book_id = create_response.json()["id"]
    
    # Update the book (by owner)
    update_data = {
        "title": "Updated Title",
        "description": "Updated description"
    }
    response = client.put(f"/books/{book_id}", json=update_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["description"] == "Updated description"
    assert data["author"] == "Original Author"  # Should remain unchanged


def test_update_book_not_found(client):
    """Test updating a non-existent book returns 404."""
    # Register and login to get token
    client.post("/register", json={
        "email": "updatenotfound@example.com",
        "password": STRONG_PASSWORD,
        "role": "user"
    })
    login_response = client.post("/login", json={
        "email": "updatenotfound@example.com",
        "password": STRONG_PASSWORD
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    update_data = {"title": "New Title"}
    response = client.put("/books/99999", json=update_data, headers=headers)
    assert response.status_code == 404


def test_delete_book(client):
    """Test deleting a book."""
    from tests.conftest import create_admin_user
    
    # Register regular user to create the book
    client.post("/register", json={
        "email": "creator@example.com",
        "password": STRONG_PASSWORD,
        "role": "user"
    })
    creator_login = client.post("/login", json={
        "email": "creator@example.com",
        "password": STRONG_PASSWORD
    })
    creator_token = creator_login.json()["access_token"]
    creator_headers = {"Authorization": f"Bearer {creator_token}"}

    # Create a test book
    book_data = {
        "title": "Book to Delete",
        "author": "Delete Author",
        "isbn": "978-4444444444",
        "published_date": "2023-01-15",
        "description": "Will be deleted"
    }
    create_response = client.post("/books", json=book_data, headers=creator_headers)
    book_id = create_response.json()["id"]
    
    # Create admin and delete the book
    create_admin_user(client, "deletebook@example.com", STRONG_PASSWORD)
    admin_login = client.post("/login", json={
        "email": "deletebook@example.com",
        "password": STRONG_PASSWORD
    })
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Delete the book
    response = client.delete(f"/books/{book_id}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json() == {"message": "Book deleted successfully"}
    
    # Verify book is deleted
    get_response = client.get(f"/books/{book_id}", headers=admin_headers)
    assert get_response.status_code == 404


def test_delete_book_not_found(client):
    """Test deleting a non-existent book returns 404."""
    from tests.conftest import create_admin_user
    
    # Create admin
    create_admin_user(client, "deletenotfound@example.com", STRONG_PASSWORD)
    admin_login = client.post("/login", json={
        "email": "deletenotfound@example.com",
        "password": STRONG_PASSWORD
    })
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.delete("/books/99999", headers=admin_headers)
    assert response.status_code == 404

