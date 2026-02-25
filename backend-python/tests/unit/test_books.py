"""
Unit tests for Book CRUD endpoints.
"""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from tests.conftest import get_auth_headers, create_test_author, create_test_book, STRONG_PASSWORD


def test_health_check(client):
    """Test the root endpoint returns correct message."""
    response = client.get("/")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["message"] == "Book Store API"
    assert response_data["version"] == "1.0.0"
    assert "docs" in response_data
    assert "health" in response_data


def test_create_book_duplicate_isbn(client):
    """Test creating a book with duplicate ISBN returns 400."""
    admin_headers = get_auth_headers(client, "admin_dup@example.com", STRONG_PASSWORD, is_admin=True)

    # Create author
    author = create_test_author(client, "Test Author", admin_headers=admin_headers)

    book_data = {
        "title": "Test Book",
        "isbn": "9781234567890",
        "published_date": "2023-01-15",
        "description": "Test description",
        "author_ids": [author["id"]],
        "category_ids": []
    }
    # Create first book
    response = client.post("/api/v1/books", json=book_data, headers=admin_headers)
    assert response.status_code == 201
    
    # Try to create duplicate
    response = client.post("/api/v1/books", json=book_data, headers=admin_headers)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_get_all_books(client):
    """Test getting all books with paginated response."""
    # Create a test book first (requires admin)
    admin_headers = get_auth_headers(client, "admin_reader@example.com", STRONG_PASSWORD, is_admin=True)
    author = create_test_author(client, "Test Author", admin_headers=admin_headers)

    book_data = {
        "title": "Test Book",
        "isbn": "9781111111111",
        "published_date": "2023-01-15",
        "description": "Test description",
        "author_ids": [author["id"]],
        "category_ids": []
    }
    client.post("/api/v1/books", json=book_data, headers=admin_headers)

    response = client.get("/api/v1/books")
    assert response.status_code == 200
    data = response.json()
    # Check for paginated response structure
    assert isinstance(data, dict)
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) > 0


def test_get_book_by_id(client):
    """Test getting a specific book by ID."""
    # Create a test book (requires admin)
    admin_headers = get_auth_headers(client, "admin_finder@example.com", STRONG_PASSWORD, is_admin=True)
    author = create_test_author(client, "Specific Author", admin_headers=admin_headers)

    book_data = {
        "title": "Specific Book",
        "isbn": "9782222222222",
        "published_date": "2023-01-15",
        "description": "Specific description",
        "author_ids": [author["id"]],
        "category_ids": []
    }
    create_response = client.post("/api/v1/books", json=book_data, headers=admin_headers)
    book_id = create_response.json()["id"]

    response = client.get(f"/api/v1/books/{book_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == book_id
    assert data["title"] == book_data["title"]


def test_get_book_by_id_not_found(client):
    """Test getting a non-existent book returns 404."""
    response = client.get("/api/v1/books/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_update_book(client):
    """Test updating a book (owner can update)."""
    # Create a test book as admin
    admin_headers = get_auth_headers(client, "admin_updater@example.com", STRONG_PASSWORD, is_admin=True)
    author = create_test_author(client, "Original Author", admin_headers=admin_headers)

    book_data = {
        "title": "Original Title",
        "isbn": "9783333333333",
        "published_date": "2023-01-15",
        "description": "Original description",
        "author_ids": [author["id"]],
        "category_ids": []
    }
    create_response = client.post("/api/v1/books", json=book_data, headers=admin_headers)
    book_id = create_response.json()["id"]

    # Update the book (same admin user is the owner)
    update_data = {
        "title": "Updated Title",
        "description": "Updated description"
    }
    response = client.put(f"/api/v1/books/{book_id}", json=update_data, headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["description"] == "Updated description"


def test_update_book_not_found(client):
    """Test updating a non-existent book returns 404."""
    admin_headers = get_auth_headers(client, "admin_update_nf@example.com", STRONG_PASSWORD, is_admin=True)
    update_data = {"title": "New Title"}
    response = client.put("/api/v1/books/99999", json=update_data, headers=admin_headers)
    assert response.status_code == 404


def test_delete_book(client):
    """Test deleting a book (requires admin)."""
    # Create a test book as admin
    admin_headers = get_auth_headers(client, "admin_deleter@example.com", STRONG_PASSWORD, is_admin=True)
    author = create_test_author(client, "Delete Author", admin_headers=admin_headers)

    book_data = {
        "title": "Book to Delete",
        "isbn": "9784444444444",
        "published_date": "2023-01-15",
        "description": "Will be deleted",
        "author_ids": [author["id"]],
        "category_ids": []
    }
    create_response = client.post("/api/v1/books", json=book_data, headers=admin_headers)
    book_id = create_response.json()["id"]

    # Delete the book (requires admin)
    response = client.delete(f"/api/v1/books/{book_id}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json() == {"message": "Book deleted successfully"}

    # Verify book is deleted
    get_response = client.get(f"/api/v1/books/{book_id}")
    assert get_response.status_code == 404


def test_delete_book_not_found(client):
    """Test deleting a non-existent book returns 404."""
    admin_headers = get_auth_headers(client, "admin_del_nf@example.com", STRONG_PASSWORD, is_admin=True)
    response = client.delete("/api/v1/books/99999", headers=admin_headers)
    assert response.status_code == 404

