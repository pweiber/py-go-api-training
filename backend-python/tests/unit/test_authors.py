"""
Unit tests for Author CRUD endpoints.
"""
import pytest
from tests.conftest import get_auth_headers, STRONG_PASSWORD


def test_create_author(client):
    """Test creating an author with valid data."""
    auth_headers = get_auth_headers(client, "author_creator@example.com", STRONG_PASSWORD, role="admin")

    author_data = {
        "name": "J.K. Rowling",
        "bio": "British author best known for the Harry Potter series",
        "birth_date": "1965-07-31",
        "nationality": "British"
    }

    response = client.post("/api/v1/authors", json=author_data, headers=auth_headers)
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == author_data["name"]
    assert data["bio"] == author_data["bio"]
    assert data["nationality"] == author_data["nationality"]
    assert "id" in data
    assert "created_at" in data


def test_create_author_validation(client):
    """Test creating an author with missing required fields."""
    auth_headers = get_auth_headers(client, "author_val@example.com", STRONG_PASSWORD, role="admin")

    # Missing name (required field)
    author_data = {
        "bio": "Some biography"
    }

    response = client.post("/api/v1/authors", json=author_data, headers=auth_headers)
    assert response.status_code == 422  # Validation error


def test_create_author_minimal(client):
    """Test creating an author with only required fields."""
    auth_headers = get_auth_headers(client, "author_min@example.com", STRONG_PASSWORD, role="admin")

    author_data = {
        "name": "Minimal Author"
    }

    response = client.post("/api/v1/authors", json=author_data, headers=auth_headers)
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == author_data["name"]
    assert data["bio"] is None
    assert data["nationality"] is None


def test_get_authors(client):
    """Test getting all authors."""
    auth_headers = get_auth_headers(client, "author_list@example.com", STRONG_PASSWORD, role="admin")

    # Create an author first
    client.post("/api/v1/authors", json={"name": "Test Author"}, headers=auth_headers)

    response = client.get("/api/v1/authors")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_author_by_id(client):
    """Test getting a specific author by ID."""
    auth_headers = get_auth_headers(client, "author_get@example.com", STRONG_PASSWORD, role="admin")

    # Create an author
    create_response = client.post("/api/v1/authors", json={"name": "Specific Author"}, headers=auth_headers)
    author_id = create_response.json()["id"]

    response = client.get(f"/api/v1/authors/{author_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == author_id
    assert data["name"] == "Specific Author"
    assert "books" in data  # Should include books relationship


def test_get_author_not_found(client):
    """Test getting a non-existent author."""
    response = client.get("/api/v1/authors/99999")
    assert response.status_code == 404


def test_get_author_with_books(client):
    """Test that author response includes their books."""
    auth_headers = get_auth_headers(client, "author_books@example.com", STRONG_PASSWORD, role="admin")

    # Create an author
    author_response = client.post("/api/v1/authors", json={"name": "Author With Books"}, headers=auth_headers)
    author_id = author_response.json()["id"]

    # Create a book linked to this author
    book_data = {
        "title": "Test Book",
        "author": "Author With Books",
        "author_id": author_id,
        "isbn": "978-1111111111",
        "published_date": "2023-01-15"
    }
    client.post("/api/v1/books", json=book_data, headers=auth_headers)

    # Get author with books
    response = client.get(f"/api/v1/authors/{author_id}")
    assert response.status_code == 200

    data = response.json()
    assert "books" in data
    assert len(data["books"]) == 1
    assert data["books"][0]["title"] == "Test Book"


def test_update_author(client):
    """Test updating an author."""
    auth_headers = get_auth_headers(client, "author_update@example.com", STRONG_PASSWORD, role="admin")

    # Create an author
    create_response = client.post("/api/v1/authors", json={"name": "Original Name"}, headers=auth_headers)
    author_id = create_response.json()["id"]

    # Update the author
    update_data = {
        "name": "Updated Name",
        "bio": "Updated biography"
    }
    response = client.put(f"/api/v1/authors/{author_id}", json=update_data, headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["bio"] == "Updated biography"


def test_delete_author_without_books(client):
    """Test deleting an author who has no books."""
    auth_headers = get_auth_headers(client, "author_del@example.com", STRONG_PASSWORD, role="admin")

    # Create an author
    create_response = client.post("/api/v1/authors", json={"name": "Author To Delete"}, headers=auth_headers)
    author_id = create_response.json()["id"]

    # Delete the author
    response = client.delete(f"/api/v1/authors/{author_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Author deleted successfully"

    # Verify deletion
    get_response = client.get(f"/api/v1/authors/{author_id}")
    assert get_response.status_code == 404


def test_delete_author_with_books(client):
    """Test that deleting an author with books returns 409 conflict."""
    auth_headers = get_auth_headers(client, "author_del_books@example.com", STRONG_PASSWORD, role="admin")

    # Create an author
    author_response = client.post("/api/v1/authors", json={"name": "Author With Books"}, headers=auth_headers)
    author_id = author_response.json()["id"]

    # Create a book linked to this author
    book_data = {
        "title": "Test Book",
        "author": "Author With Books",
        "author_id": author_id,
        "isbn": "978-2222222222",
        "published_date": "2023-01-15"
    }
    client.post("/api/v1/books", json=book_data, headers=auth_headers)

    # Try to delete the author (should fail)
    response = client.delete(f"/api/v1/authors/{author_id}", headers=auth_headers)
    assert response.status_code == 409
    assert "book(s)" in response.json()["detail"]


def test_delete_author_requires_admin(client):
    """Test that only admins can delete authors."""
    admin_headers = get_auth_headers(client, "admin_auth@example.com", STRONG_PASSWORD, role="admin")
    user_headers = get_auth_headers(client, "regular_user@example.com", STRONG_PASSWORD)

    # Create an author as admin
    create_response = client.post("/api/v1/authors", json={"name": "Admin Created"}, headers=admin_headers)
    author_id = create_response.json()["id"]

    # Try to delete as regular user
    response = client.delete(f"/api/v1/authors/{author_id}", headers=user_headers)
    assert response.status_code == 403


def test_create_author_requires_admin(client):
    """Test that only admins can create authors."""
    user_headers = get_auth_headers(client, "regular_user_create@example.com", STRONG_PASSWORD)

    author_data = {
        "name": "Unauthorized Author",
        "bio": "This should not be created"
    }

    response = client.post("/api/v1/authors", json=author_data, headers=user_headers)
    assert response.status_code == 403


def test_update_author_requires_admin(client):
    """Test that only admins can update authors."""
    admin_headers = get_auth_headers(client, "admin_update@example.com", STRONG_PASSWORD, role="admin")
    user_headers = get_auth_headers(client, "regular_user_update@example.com", STRONG_PASSWORD)

    # Create an author as admin
    create_response = client.post("/api/v1/authors", json={"name": "Test Author"}, headers=admin_headers)
    author_id = create_response.json()["id"]

    # Try to update as regular user
    update_data = {
        "name": "Hacked Name",
        "bio": "Unauthorized update"
    }
    response = client.put(f"/api/v1/authors/{author_id}", json=update_data, headers=user_headers)
    assert response.status_code == 403



