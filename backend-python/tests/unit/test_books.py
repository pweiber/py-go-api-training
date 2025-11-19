"""
Unit tests for Book CRUD endpoints.
"""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


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
    book_data = {
        "title": "Test Book",
        "author": "Test Author",
        "isbn": "978-1234567890",
        "published_date": "2023-01-15",
        "description": "Test description"
    }
    # Create first book
    response = client.post("/books", json=book_data)
    assert response.status_code == 201
    
    # Try to create duplicate
    response = client.post("/books", json=book_data)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_get_all_books(client):
    """Test getting all books."""
    # Create a test book first
    book_data = {
        "title": "Test Book",
        "author": "Test Author",
        "isbn": "978-1111111111",
        "published_date": "2023-01-15",
        "description": "Test description"
    }
    client.post("/books", json=book_data)
    
    response = client.get("/books")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_book_by_id(client):
    """Test getting a specific book by ID."""
    # Create a test book
    book_data = {
        "title": "Specific Book",
        "author": "Specific Author",
        "isbn": "978-2222222222",
        "published_date": "2023-01-15",
        "description": "Specific description"
    }
    create_response = client.post("/books", json=book_data)
    book_id = create_response.json()["id"]
    
    response = client.get(f"/books/{book_id}")
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
    """Test updating a book."""
    # Create a test book
    book_data = {
        "title": "Original Title",
        "author": "Original Author",
        "isbn": "978-3333333333",
        "published_date": "2023-01-15",
        "description": "Original description"
    }
    create_response = client.post("/books", json=book_data)
    book_id = create_response.json()["id"]
    
    # Update the book
    update_data = {
        "title": "Updated Title",
        "description": "Updated description"
    }
    response = client.put(f"/books/{book_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["description"] == "Updated description"
    assert data["author"] == "Original Author"  # Should remain unchanged


def test_update_book_not_found(client):
    """Test updating a non-existent book returns 404."""
    update_data = {"title": "New Title"}
    response = client.put("/books/99999", json=update_data)
    assert response.status_code == 404


def test_delete_book(client):
    """Test deleting a book."""
    # Create a test book
    book_data = {
        "title": "Book to Delete",
        "author": "Delete Author",
        "isbn": "978-4444444444",
        "published_date": "2023-01-15",
        "description": "Will be deleted"
    }
    create_response = client.post("/books", json=book_data)
    book_id = create_response.json()["id"]
    
    # Delete the book
    response = client.delete(f"/books/{book_id}")
    assert response.status_code == 200
    assert response.json() == {"message": "Book deleted successfully"}
    
    # Verify book is deleted
    get_response = client.get(f"/books/{book_id}")
    assert get_response.status_code == 404


def test_delete_book_not_found(client):
    """Test deleting a non-existent book returns 404."""
    response = client.delete("/books/99999")
    assert response.status_code == 404

