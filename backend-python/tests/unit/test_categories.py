"""
Unit tests for Category CRUD endpoints.
"""
import pytest
from tests.conftest import get_auth_headers, STRONG_PASSWORD


def test_create_category(client):
    """Test creating a category with valid data."""
    auth_headers = get_auth_headers(client, "cat_creator@example.com", STRONG_PASSWORD, role="admin")

    category_data = {
        "name": "Fantasy",
        "description": "Fantasy and magical fiction books"
    }

    response = client.post("/api/v1/categories", json=category_data, headers=auth_headers)
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == category_data["name"]
    assert data["description"] == category_data["description"]
    assert "id" in data
    assert "created_at" in data


def test_create_category_requires_admin(client):
    """Test that only admins can create categories."""
    user_headers = get_auth_headers(client, "regular_cat@example.com", STRONG_PASSWORD)

    category_data = {
        "name": "Science Fiction"
    }

    response = client.post("/api/v1/categories", json=category_data, headers=user_headers)
    assert response.status_code == 403


def test_create_category_duplicate_name(client):
    """Test creating a category with duplicate name."""
    auth_headers = get_auth_headers(client, "cat_dup@example.com", STRONG_PASSWORD, role="admin")

    category_data = {"name": "Duplicate Category"}

    # Create first category
    response = client.post("/api/v1/categories", json=category_data, headers=auth_headers)
    assert response.status_code == 201

    # Try to create duplicate
    response = client.post("/api/v1/categories", json=category_data, headers=auth_headers)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_get_categories(client):
    """Test getting all categories."""
    auth_headers = get_auth_headers(client, "cat_list@example.com", STRONG_PASSWORD, role="admin")

    # Create a category first
    client.post("/api/v1/categories", json={"name": "Test Category"}, headers=auth_headers)

    response = client.get("/api/v1/categories")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_category_by_id(client):
    """Test getting a specific category by ID with its books."""
    auth_headers = get_auth_headers(client, "cat_get@example.com", STRONG_PASSWORD, role="admin")

    # Create a category
    create_response = client.post("/api/v1/categories", json={"name": "Specific Category"}, headers=auth_headers)
    category_id = create_response.json()["id"]

    response = client.get(f"/api/v1/categories/{category_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == category_id
    assert data["name"] == "Specific Category"
    assert "books" in data  # Should include books relationship


def test_assign_multiple_categories(client):
    """Test that a book can have multiple categories."""
    auth_headers = get_auth_headers(client, "multi_cat@example.com", STRONG_PASSWORD, role="admin")

    # Create categories
    cat1_response = client.post("/api/v1/categories", json={"name": "Category 1"}, headers=auth_headers)
    cat2_response = client.post("/api/v1/categories", json={"name": "Category 2"}, headers=auth_headers)
    cat3_response = client.post("/api/v1/categories", json={"name": "Category 3"}, headers=auth_headers)

    cat1_id = cat1_response.json()["id"]
    cat2_id = cat2_response.json()["id"]
    cat3_id = cat3_response.json()["id"]

    # Create a book
    book_data = {
        "title": "Multi-Category Book",
        "author": "Test Author",
        "isbn": "978-3333333333",
        "published_date": "2023-01-15"
    }
    book_response = client.post("/api/v1/books", json=book_data, headers=auth_headers)
    book_id = book_response.json()["id"]

    # Assign multiple categories
    response = client.put(
        f"/api/v1/books/{book_id}/categories",
        json={"category_ids": [cat1_id, cat2_id, cat3_id]},
        headers=auth_headers
    )
    assert response.status_code == 200

    # Verify book has categories
    book_response = client.get(f"/api/v1/books/{book_id}")
    assert book_response.status_code == 200
    data = book_response.json()
    assert len(data["categories"]) == 3


def test_category_has_many_books(client):
    """Test that a category can have many books."""
    auth_headers = get_auth_headers(client, "cat_books@example.com", STRONG_PASSWORD, role="admin")

    # Create a category
    cat_response = client.post("/api/v1/categories", json={"name": "Multi-Book Category"}, headers=auth_headers)
    cat_id = cat_response.json()["id"]

    # Create multiple books and assign to category
    for i in range(3):
        book_data = {
            "title": f"Book {i+1}",
            "author": "Test Author",
            "isbn": f"978-444444444{i}",
            "published_date": "2023-01-15"
        }
        book_response = client.post("/api/v1/books", json=book_data, headers=auth_headers)
        book_id = book_response.json()["id"]

        # Assign category
        client.put(
            f"/api/v1/books/{book_id}/categories",
            json={"category_ids": [cat_id]},
            headers=auth_headers
        )

    # Get category with books
    response = client.get(f"/api/v1/categories/{cat_id}")
    assert response.status_code == 200

    data = response.json()
    assert len(data["books"]) == 3


def test_remove_category_from_book(client):
    """Test removing a category from a book."""
    auth_headers = get_auth_headers(client, "remove_cat@example.com", STRONG_PASSWORD, role="admin")

    # Create categories
    cat1_response = client.post("/api/v1/categories", json={"name": "Keep Category"}, headers=auth_headers)
    cat2_response = client.post("/api/v1/categories", json={"name": "Remove Category"}, headers=auth_headers)

    cat1_id = cat1_response.json()["id"]
    cat2_id = cat2_response.json()["id"]

    # Create a book
    book_data = {
        "title": "Category Test Book",
        "author": "Test Author",
        "isbn": "978-5555555555",
        "published_date": "2023-01-15"
    }
    book_response = client.post("/api/v1/books", json=book_data, headers=auth_headers)
    book_id = book_response.json()["id"]

    # Assign both categories
    client.put(
        f"/api/v1/books/{book_id}/categories",
        json={"category_ids": [cat1_id, cat2_id]},
        headers=auth_headers
    )

    # Remove one category by updating with only one
    response = client.put(
        f"/api/v1/books/{book_id}/categories",
        json={"category_ids": [cat1_id]},
        headers=auth_headers
    )
    assert response.status_code == 200

    # Verify book has only one category
    book_response = client.get(f"/api/v1/books/{book_id}")
    data = book_response.json()
    assert len(data["categories"]) == 1
    assert data["categories"][0]["id"] == cat1_id


def test_update_category(client):
    """Test updating a category."""
    auth_headers = get_auth_headers(client, "cat_update@example.com", STRONG_PASSWORD, role="admin")

    # Create a category
    create_response = client.post("/api/v1/categories", json={"name": "Original Category"}, headers=auth_headers)
    category_id = create_response.json()["id"]

    # Update the category
    update_data = {
        "name": "Updated Category",
        "description": "Updated description"
    }
    response = client.put(f"/api/v1/categories/{category_id}", json=update_data, headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "Updated Category"
    assert data["description"] == "Updated description"


def test_delete_category(client):
    """Test deleting a category."""
    auth_headers = get_auth_headers(client, "cat_delete@example.com", STRONG_PASSWORD, role="admin")

    # Create a category
    create_response = client.post("/api/v1/categories", json={"name": "Category To Delete"}, headers=auth_headers)
    category_id = create_response.json()["id"]

    # Delete the category
    response = client.delete(f"/api/v1/categories/{category_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Category deleted successfully"

    # Verify deletion
    get_response = client.get(f"/api/v1/categories/{category_id}")
    assert get_response.status_code == 404


def test_assign_nonexistent_category(client):
    """Test assigning a nonexistent category to a book."""
    auth_headers = get_auth_headers(client, "bad_cat@example.com", STRONG_PASSWORD, role="admin")

    # Create a book
    book_data = {
        "title": "Test Book",
        "author": "Test Author",
        "isbn": "978-6666666666",
        "published_date": "2023-01-15"
    }
    book_response = client.post("/api/v1/books", json=book_data, headers=auth_headers)
    book_id = book_response.json()["id"]

    # Try to assign nonexistent category
    response = client.put(
        f"/api/v1/books/{book_id}/categories",
        json={"category_ids": [99999]},
        headers=auth_headers
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

