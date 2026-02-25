"""
Tests for error handling and edge cases to increase coverage.
"""
import pytest
from tests.conftest import get_auth_headers, STRONG_PASSWORD


def test_create_book_invalid_date_format(client):
    """Test creating a book with invalid date format."""
    admin_headers = get_auth_headers(client, "admin_date@test.com", STRONG_PASSWORD, is_admin=True)

    book_data = {
        "title": "Invalid Date Book",
        "isbn": "9781234567890",
        "published_date": "2024/01/01",  # Wrong format
        "description": "Test",
        "author_ids": [],
        "category_ids": []
    }

    response = client.post("/api/v1/books", json=book_data, headers=admin_headers)
    assert response.status_code in [400, 422]


def test_create_book_with_nonexistent_author(client):
    """Test creating a book with non-existent author ID."""
    admin_headers = get_auth_headers(client, "admin_auth@test.com", STRONG_PASSWORD, is_admin=True)

    book_data = {
        "title": "Invalid Author Book",
        "isbn": "9781234567890",
        "published_date": "2024-01-01",
        "description": "Test",
        "author_ids": [99999],  # Non-existent author
        "category_ids": []
    }

    response = client.post("/api/v1/books", json=book_data, headers=admin_headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_create_book_with_nonexistent_category(client):
    """Test creating a book with non-existent category ID."""
    admin_headers = get_auth_headers(client, "admin_cat@test.com", STRONG_PASSWORD, is_admin=True)

    book_data = {
        "title": "Invalid Category Book",
        "isbn": "9781234567890",
        "published_date": "2024-01-01",
        "description": "Test",
        "author_ids": [],
        "category_ids": [99999]  # Non-existent category
    }

    response = client.post("/api/v1/books", json=book_data, headers=admin_headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_update_book_with_nonexistent_author(client):
    """Test updating a book with non-existent author ID."""
    admin_headers = get_auth_headers(client, "admin_upd@test.com", STRONG_PASSWORD, is_admin=True)

    # Create a book first
    book_data = {
        "title": "Test Book",
        "isbn": "9781234567890",
        "published_date": "2024-01-01",
        "description": "Test",
        "author_ids": [],
        "category_ids": []
    }
    create_response = client.post("/api/v1/books", json=book_data, headers=admin_headers)
    book_id = create_response.json()["id"]

    # Try to update with non-existent author
    update_data = {
        "author_ids": [99999]
    }

    response = client.put(f"/api/v1/books/{book_id}", json=update_data, headers=admin_headers)
    assert response.status_code == 404


def test_update_book_with_nonexistent_category(client):
    """Test updating a book with non-existent category ID."""
    admin_headers = get_auth_headers(client, "admin_updc@test.com", STRONG_PASSWORD, is_admin=True)

    # Create a book first
    book_data = {
        "title": "Test Book",
        "isbn": "9781234567891",
        "published_date": "2024-01-01",
        "description": "Test",
        "author_ids": [],
        "category_ids": []
    }
    create_response = client.post("/api/v1/books", json=book_data, headers=admin_headers)
    book_id = create_response.json()["id"]

    # Try to update with non-existent category
    update_data = {
        "category_ids": [99999]
    }

    response = client.put(f"/api/v1/books/{book_id}", json=update_data, headers=admin_headers)
    assert response.status_code == 404


def test_update_nonexistent_book(client):
    """Test updating a book that doesn't exist."""
    admin_headers = get_auth_headers(client, "admin_noupd@test.com", STRONG_PASSWORD, is_admin=True)

    update_data = {
        "title": "Updated Title"
    }

    response = client.put("/api/v1/books/99999", json=update_data, headers=admin_headers)
    assert response.status_code == 404


def test_delete_nonexistent_book(client):
    """Test deleting a book that doesn't exist."""
    admin_headers = get_auth_headers(client, "admin_nodel@test.com", STRONG_PASSWORD, is_admin=True)

    response = client.delete("/api/v1/books/99999", headers=admin_headers)
    assert response.status_code == 404


def test_create_author_requires_admin(client):
    """Test that only admins can create authors."""
    user_headers = get_auth_headers(client, "user_author@test.com", STRONG_PASSWORD, role="user")

    author_data = {
        "name": "Test Author"
    }

    response = client.post("/api/v1/authors", json=author_data, headers=user_headers)
    assert response.status_code == 403


def test_update_author_requires_admin(client):
    """Test that only admins can update authors."""
    admin_headers = get_auth_headers(client, "admin_author@test.com", STRONG_PASSWORD, is_admin=True)
    user_headers = get_auth_headers(client, "user_author2@test.com", STRONG_PASSWORD, role="user")

    # Create author as admin
    create_response = client.post("/api/v1/authors", json={"name": "Test Author"}, headers=admin_headers)
    author_id = create_response.json()["id"]

    # Try to update as user
    update_data = {"name": "Updated Name"}
    response = client.put(f"/api/v1/authors/{author_id}", json=update_data, headers=user_headers)
    assert response.status_code == 403


def test_delete_author_requires_admin(client):
    """Test that only admins can delete authors."""
    admin_headers = get_auth_headers(client, "admin_author3@test.com", STRONG_PASSWORD, is_admin=True)
    user_headers = get_auth_headers(client, "user_author3@test.com", STRONG_PASSWORD, role="user")

    # Create author as admin
    create_response = client.post("/api/v1/authors", json={"name": "Test Author"}, headers=admin_headers)
    author_id = create_response.json()["id"]

    # Try to delete as user
    response = client.delete(f"/api/v1/authors/{author_id}", headers=user_headers)
    assert response.status_code == 403


def test_update_category_requires_admin(client):
    """Test that only admins can update categories."""
    admin_headers = get_auth_headers(client, "admin_cat2@test.com", STRONG_PASSWORD, is_admin=True)
    user_headers = get_auth_headers(client, "user_cat@test.com", STRONG_PASSWORD, role="user")

    # Create category as admin
    create_response = client.post("/api/v1/categories", json={"name": "Test Category"}, headers=admin_headers)
    category_id = create_response.json()["id"]

    # Try to update as user
    update_data = {"name": "Updated Category"}
    response = client.put(f"/api/v1/categories/{category_id}", json=update_data, headers=user_headers)
    assert response.status_code == 403


def test_delete_category_requires_admin(client):
    """Test that only admins can delete categories."""
    admin_headers = get_auth_headers(client, "admin_cat3@test.com", STRONG_PASSWORD, is_admin=True)
    user_headers = get_auth_headers(client, "user_cat2@test.com", STRONG_PASSWORD, role="user")

    # Create category as admin
    create_response = client.post("/api/v1/categories", json={"name": "Test Category"}, headers=admin_headers)
    category_id = create_response.json()["id"]

    # Try to delete as user
    response = client.delete(f"/api/v1/categories/{category_id}", headers=user_headers)
    assert response.status_code == 403


def test_list_books_with_category_filter(client):
    """Test filtering books by category name."""
    admin_headers = get_auth_headers(client, "admin_filter@test.com", STRONG_PASSWORD, is_admin=True)

    # Create a category
    cat_response = client.post("/api/v1/categories", json={"name": "Science Fiction"}, headers=admin_headers)
    category_id = cat_response.json()["id"]

    # Create a book in that category
    book_data = {
        "title": "Sci-Fi Book",
        "isbn": "9781234567890",
        "published_date": "2024-01-01",
        "description": "A science fiction book",
        "author_ids": [],
        "category_ids": [category_id]
    }
    client.post("/api/v1/books", json=book_data, headers=admin_headers)

    # Filter by category name
    response = client.get("/api/v1/books?category=Science Fiction")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


def test_list_books_with_min_rating_filter(client):
    """Test filtering books by minimum rating."""
    response = client.get("/api/v1/books?min_rating=4.0")
    assert response.status_code == 200
    # Should return successfully even if no books match


def test_list_books_with_invalid_page(client):
    """Test listing books with invalid page number."""
    response = client.get("/api/v1/books?page=0")
    assert response.status_code == 422  # Validation error


def test_list_books_with_invalid_size(client):
    """Test listing books with invalid page size."""
    response = client.get("/api/v1/books?size=1000")
    assert response.status_code == 422  # Exceeds max size


def test_update_author_not_found(client):
    """Test updating a non-existent author."""
    admin_headers = get_auth_headers(client, "admin_noauth@test.com", STRONG_PASSWORD, is_admin=True)

    update_data = {"name": "Updated Name"}
    response = client.put("/api/v1/authors/99999", json=update_data, headers=admin_headers)
    assert response.status_code == 404


def test_delete_author_not_found(client):
    """Test deleting a non-existent author."""
    admin_headers = get_auth_headers(client, "admin_nodel2@test.com", STRONG_PASSWORD, is_admin=True)

    response = client.delete("/api/v1/authors/99999", headers=admin_headers)
    assert response.status_code == 404


def test_update_category_not_found(client):
    """Test updating a non-existent category."""
    admin_headers = get_auth_headers(client, "admin_nocat@test.com", STRONG_PASSWORD, is_admin=True)

    update_data = {"name": "Updated Category"}
    response = client.put("/api/v1/categories/99999", json=update_data, headers=admin_headers)
    assert response.status_code == 404


def test_delete_category_not_found(client):
    """Test deleting a non-existent category."""
    admin_headers = get_auth_headers(client, "admin_nodel3@test.com", STRONG_PASSWORD, is_admin=True)

    response = client.delete("/api/v1/categories/99999", headers=admin_headers)
    assert response.status_code == 404

