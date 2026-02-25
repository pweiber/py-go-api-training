"""
Unit tests for Category CRUD endpoints.
"""
import pytest
from tests.conftest import get_auth_headers, create_test_author, create_test_book, create_test_category, STRONG_PASSWORD


def test_create_category(client):
    """Test creating a category with valid data."""
    auth_headers = get_auth_headers(client, "cat_creator@example.com", STRONG_PASSWORD, is_admin=True)

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
    auth_headers = get_auth_headers(client, "cat_dup@example.com", STRONG_PASSWORD, is_admin=True)

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
    auth_headers = get_auth_headers(client, "cat_list@example.com", STRONG_PASSWORD, is_admin=True)

    # Create a category first
    client.post("/api/v1/categories", json={"name": "Test Category"}, headers=auth_headers)

    response = client.get("/api/v1/categories")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_category_by_id(client):
    """Test getting a specific category by ID with its books."""
    auth_headers = get_auth_headers(client, "cat_get@example.com", STRONG_PASSWORD, is_admin=True)

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
    admin_headers = get_auth_headers(client, "multi_cat@example.com", STRONG_PASSWORD, is_admin=True)

    # Create categories
    cat1 = create_test_category(client, "Category 1", admin_headers=admin_headers)
    cat2 = create_test_category(client, "Category 2", admin_headers=admin_headers)
    cat3 = create_test_category(client, "Category 3", admin_headers=admin_headers)

    # Create a book with an author
    author = create_test_author(client, "Test Author", admin_headers=admin_headers)
    book = create_test_book(
        client,
        title="Multi-Category Book",
        isbn="9783333333333",
        published_date="2023-01-15",
        author_ids=[author["id"]],
        admin_headers=admin_headers
    )
    book_id = book["id"]

    # Assign multiple categories
    response = client.put(
        f"/api/v1/books/{book_id}/categories",
        json={"category_ids": [cat1["id"], cat2["id"], cat3["id"]]},
        headers=admin_headers
    )
    assert response.status_code == 200

    # Verify book has categories
    book_response = client.get(f"/api/v1/books/{book_id}")
    assert book_response.status_code == 200
    data = book_response.json()
    assert len(data["categories"]) == 3


def test_category_has_many_books(client):
    """Test that a category can have many books."""
    admin_headers = get_auth_headers(client, "cat_books@example.com", STRONG_PASSWORD, is_admin=True)

    # Create a category and author
    category = create_test_category(client, "Multi-Book Category", admin_headers=admin_headers)
    author = create_test_author(client, "Test Author", admin_headers=admin_headers)

    # Create multiple books and assign to category
    for i in range(3):
        book = create_test_book(
            client,
            title=f"Book {i+1}",
            isbn=f"978444444444{i}",
            published_date="2023-01-15",
            author_ids=[author["id"]],
            admin_headers=admin_headers
        )

        # Assign category
        client.put(
            f"/api/v1/books/{book['id']}/categories",
            json={"category_ids": [category["id"]]},
            headers=admin_headers
        )

    # Get category with books
    response = client.get(f"/api/v1/categories/{category['id']}")
    assert response.status_code == 200

    data = response.json()
    assert len(data["books"]) == 3


def test_remove_category_from_book(client):
    """Test removing a category from a book."""
    admin_headers = get_auth_headers(client, "remove_cat@example.com", STRONG_PASSWORD, is_admin=True)

    # Create categories and author
    cat1 = create_test_category(client, "Keep Category", admin_headers=admin_headers)
    cat2 = create_test_category(client, "Remove Category", admin_headers=admin_headers)
    author = create_test_author(client, "Test Author", admin_headers=admin_headers)

    # Create a book
    book = create_test_book(
        client,
        title="Category Test Book",
        isbn="9785555555555",
        published_date="2023-01-15",
        author_ids=[author["id"]],
        admin_headers=admin_headers
    )
    book_id = book["id"]

    # Assign both categories
    client.put(
        f"/api/v1/books/{book_id}/categories",
        json={"category_ids": [cat1["id"], cat2["id"]]},
        headers=admin_headers
    )

    # Remove one category by updating with only one
    response = client.put(
        f"/api/v1/books/{book_id}/categories",
        json={"category_ids": [cat1["id"]]},
        headers=admin_headers
    )
    assert response.status_code == 200

    # Verify book has only one category
    book_response = client.get(f"/api/v1/books/{book_id}")
    data = book_response.json()
    assert len(data["categories"]) == 1
    assert data["categories"][0]["id"] == cat1["id"]


def test_update_category(client):
    """Test updating a category."""
    auth_headers = get_auth_headers(client, "cat_update@example.com", STRONG_PASSWORD, is_admin=True)

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
    auth_headers = get_auth_headers(client, "cat_delete@example.com", STRONG_PASSWORD, is_admin=True)

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
    admin_headers = get_auth_headers(client, "bad_cat@example.com", STRONG_PASSWORD, is_admin=True)

    # Create a book with author
    author = create_test_author(client, "Test Author", admin_headers=admin_headers)
    book = create_test_book(
        client,
        title="Test Book",
        isbn="9786666666666",
        published_date="2023-01-15",
        author_ids=[author["id"]],
        admin_headers=admin_headers
    )

    # Try to assign nonexistent category
    response = client.put(
        f"/api/v1/books/{book['id']}/categories",
        json={"category_ids": [99999]},
        headers=admin_headers
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

