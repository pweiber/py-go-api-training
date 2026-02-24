"""
Unit tests for Books API endpoints.
Tests CRUD operations, pagination, filtering, and authorization.
"""

import pytest
from datetime import datetime

# Strong password for all tests
STRONG_PASSWORD = "TestPassword123!"


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_book_data():
    """Sample book data for testing."""
    return {
        "title": "Test Book",
        "isbn": "978-0-123456-78-9",
        "published_date": "2024-01-15",
        "description": "A test book description",
        "author_ids": [],
        "category_ids": []
    }


@pytest.fixture
def create_author(client):
    """Helper to create an author."""

    def _create_author(name="Test Author", bio="Test bio", headers=None):
        from tests.conftest import get_auth_headers

        if headers is None:
            headers = get_auth_headers(client, "admin@test.com", STRONG_PASSWORD, is_admin=True)

        response = client.post(
            "/api/v1/authors",
            json={"name": name, "bio": bio},
            headers=headers
        )
        assert response.status_code == 201
        return response.json()

    return _create_author


@pytest.fixture
def create_category(client):
    """Helper to create a category."""

    def _create_category(name="Test Category", description="Test desc", headers=None):
        from tests.conftest import get_auth_headers

        if headers is None:
            headers = get_auth_headers(client, "admin@test.com", STRONG_PASSWORD, is_admin=True)

        response = client.post(
            "/api/v1/categories",
            json={"name": name, "description": description},
            headers=headers
        )
        assert response.status_code == 201
        return response.json()

    return _create_category


@pytest.fixture
def create_book(client, create_author, create_category):
    """Helper to create a book with authors and categories."""
    counter = [0]  # Use list to allow modification in nested function

    def _create_book(
            title="Test Book",
            isbn="978-0-123456-78-9",
            with_author=True,
            with_category=True,
            headers=None
    ):
        from tests.conftest import get_auth_headers

        if headers is None:
            headers = get_auth_headers(client, "admin@test.com", STRONG_PASSWORD, is_admin=True)

        counter[0] += 1
        unique_suffix = counter[0]

        author_ids = []
        if with_author:
            author = create_author(name=f"Test Author {unique_suffix}", headers=headers)
            author_ids = [author["id"]]

        category_ids = []
        if with_category:
            category = create_category(name=f"Test Category {unique_suffix}", headers=headers)
            category_ids = [category["id"]]

        book_data = {
            "title": title,
            "isbn": isbn,
            "published_date": "2024-01-15",
            "description": "Test description",
            "author_ids": author_ids,
            "category_ids": category_ids
        }

        response = client.post("/api/v1/books", json=book_data, headers=headers)
        assert response.status_code == 201
        return response.json()

    return _create_book


# ============================================================================
# TEST: LIST BOOKS (GET /api/v1/books)
# ============================================================================

def test_list_books_empty(client):
    """Test listing books when none exist."""
    response = client.get("/api/v1/books")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data
    assert data["total"] == 0
    assert len(data["items"]) == 0


def test_list_books_with_data(client, create_book):
    """Test listing books with multiple entries."""
    # Create 3 books
    book1 = create_book(title="Book One", isbn="978-1-111111-11-1")
    book2 = create_book(title="Book Two", isbn="978-2-222222-22-2")
    book3 = create_book(title="Book Three", isbn="978-3-333333-33-3")

    response = client.get("/api/v1/books")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 3
    assert len(data["items"]) >= 3

    # Verify book data structure
    for book in data["items"][:3]:
        assert "id" in book
        assert "title" in book
        assert "isbn" in book
        assert "published_date" in book
        assert "authors" in book
        assert "categories" in book


def test_list_books_pagination(client, create_book):
    """Test book listing with pagination."""
    # Create 5 books
    for i in range(5):
        create_book(title=f"Book {i}", isbn=f"978-{i}-{i}{i}{i}{i}{i}{i}-{i}{i}-{i}")

    # Get first page (2 items)
    response = client.get("/api/v1/books?page=1&size=2")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["size"] == 2
    assert len(data["items"]) == 2
    assert data["total"] >= 5

    # Get second page
    response = client.get("/api/v1/books?page=2&size=2")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 2
    assert len(data["items"]) == 2


def test_list_books_search_by_title(client, create_book):
    """Test searching books by title."""
    create_book(title="Python Programming", isbn="978-1-111111-11-1")
    create_book(title="JavaScript Guide", isbn="978-2-222222-22-2")
    create_book(title="Python Advanced", isbn="978-3-333333-33-3")

    # Search for "Python"
    response = client.get("/api/v1/books?search=Python")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2

    # All results should contain "Python" in title
    for book in data["items"]:
        assert "Python" in book["title"]


def test_list_books_filter_by_author(client, create_book, create_author):
    """Test filtering books by author ID."""
    from tests.conftest import get_auth_headers

    admin_headers = get_auth_headers(client, "admin@test.com", STRONG_PASSWORD, "admin")

    # Create two authors
    author1 = create_author(name="Author One", headers=admin_headers)
    author2 = create_author(name="Author Two", headers=admin_headers)

    # Create books for each author
    book1_data = {
        "title": "Book by Author One",
        "isbn": "978-1-111111-11-1",
        "published_date": "2024-01-15",
        "description": "Test",
        "author_ids": [author1["id"]],
        "category_ids": []
    }
    client.post("/api/v1/books", json=book1_data, headers=admin_headers)

    book2_data = {
        "title": "Book by Author Two",
        "isbn": "978-2-222222-22-2",
        "published_date": "2024-01-15",
        "description": "Test",
        "author_ids": [author2["id"]],
        "category_ids": []
    }
    client.post("/api/v1/books", json=book2_data, headers=admin_headers)

    # Filter by author1
    response = client.get(f"/api/v1/books?author_id={author1['id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1

    # All books should have author1
    for book in data["items"]:
        author_ids = [author["id"] for author in book["authors"]]
        assert author1["id"] in author_ids


def test_list_books_filter_by_category(client, create_book, create_category):
    """Test filtering books by category name."""
    from tests.conftest import get_auth_headers

    admin_headers = get_auth_headers(client, "admin@test.com", STRONG_PASSWORD, is_admin=True)

    # Create categories
    category1 = create_category(name="Fiction", headers=admin_headers)
    category2 = create_category(name="Science", headers=admin_headers)

    # Create books in different categories
    book1_data = {
        "title": "Fiction Book",
        "isbn": "978-1-111111-11-1",
        "published_date": "2024-01-15",
        "description": "Test",
        "author_ids": [],
        "category_ids": [category1["id"]]
    }
    client.post("/api/v1/books", json=book1_data, headers=admin_headers)

    book2_data = {
        "title": "Science Book",
        "isbn": "978-2-222222-22-2",
        "published_date": "2024-01-15",
        "description": "Test",
        "author_ids": [],
        "category_ids": [category2["id"]]
    }
    client.post("/api/v1/books", json=book2_data, headers=admin_headers)

    # Filter by category name (API uses 'category' param with name, not ID)
    response = client.get(f"/api/v1/books?category=Fiction")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1

    # All books should have category1
    for book in data["items"]:
        category_ids = [cat["id"] for cat in book["categories"]]
        assert category1["id"] in category_ids


# ============================================================================
# TEST: GET BOOK BY ID (GET /api/v1/books/{id})
# ============================================================================

def test_get_book_by_id_success(client, create_book):
    """Test retrieving a specific book by ID."""
    book = create_book(title="Specific Book", isbn="978-1-234567-89-0")

    response = client.get(f"/api/v1/books/{book['id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == book["id"]
    assert data["title"] == "Specific Book"
    assert data["isbn"] == "9781234567890"  # ISBN is normalized (hyphens removed)
    assert "authors" in data
    assert "categories" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_get_book_by_id_not_found(client):
    """Test getting non-existent book returns 404."""
    response = client.get("/api/v1/books/99999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_book_by_id_invalid_id(client):
    """Test getting book with invalid ID format."""
    response = client.get("/api/v1/books/invalid")

    # Should return 422 (validation error) or 404
    assert response.status_code in [404, 422]


# ============================================================================
# TEST: CREATE BOOK (POST /api/v1/books)
# ============================================================================

def test_create_book_as_admin_success(client, sample_book_data):
    """Test that admin can create a book."""
    from tests.conftest import get_auth_headers

    admin_headers = get_auth_headers(client, "admin@test.com", STRONG_PASSWORD, is_admin=True)

    response = client.post("/api/v1/books", json=sample_book_data, headers=admin_headers)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == sample_book_data["title"]
    assert data["isbn"] == "9780123456789"  # ISBN is normalized (hyphens removed)
    assert "id" in data
    assert "created_at" in data


def test_create_book_with_authors_and_categories(client, create_author, create_category):
    """Test creating book with authors and categories."""
    from tests.conftest import get_auth_headers

    admin_headers = get_auth_headers(client, "admin@test.com", STRONG_PASSWORD, is_admin=True)

    # Create author and category
    author = create_author(headers=admin_headers)
    category = create_category(headers=admin_headers)

    book_data = {
        "title": "Complete Book",
        "isbn": "978-1-234567-89-0",
        "published_date": "2024-01-15",
        "description": "Book with author and category",
        "author_ids": [author["id"]],
        "category_ids": [category["id"]]
    }

    response = client.post("/api/v1/books", json=book_data, headers=admin_headers)

    assert response.status_code == 201
    data = response.json()
    assert len(data["authors"]) == 1
    assert data["authors"][0]["id"] == author["id"]
    assert len(data["categories"]) == 1
    assert data["categories"][0]["id"] == category["id"]


def test_create_book_as_user_forbidden(client, sample_book_data):
    """Test that regular users cannot create books."""
    from tests.conftest import get_auth_headers

    user_headers = get_auth_headers(client, "user@test.com", STRONG_PASSWORD, is_admin=False)

    response = client.post("/api/v1/books", json=sample_book_data, headers=user_headers)

    assert response.status_code == 403
    assert "admin" in response.json()["detail"].lower()


def test_create_book_without_auth_unauthorized(client, sample_book_data):
    """Test that unauthenticated requests cannot create books."""
    response = client.post("/api/v1/books", json=sample_book_data)

    assert response.status_code == 401


def test_create_book_missing_required_fields(client):
    """Test creating book with missing required fields."""
    from tests.conftest import get_auth_headers

    admin_headers = get_auth_headers(client, "admin@test.com", STRONG_PASSWORD, "admin")

    # Missing title and ISBN
    invalid_data = {
        "published_date": "2024-01-15",
        "description": "Missing title"
    }

    response = client.post("/api/v1/books", json=invalid_data, headers=admin_headers)

    assert response.status_code == 422  # Validation error


def test_create_book_invalid_isbn_format(client):
    """Test creating book with invalid ISBN format."""
    from tests.conftest import get_auth_headers

    admin_headers = get_auth_headers(client, "admin@test.com", STRONG_PASSWORD, "admin")

    invalid_data = {
        "title": "Invalid ISBN Book",
        "isbn": "invalid-isbn",  # Invalid format
        "published_date": "2024-01-15",
        "description": "Test",
        "author_ids": [],
        "category_ids": []
    }

    response = client.post("/api/v1/books", json=invalid_data, headers=admin_headers)

    # Should return 422 validation error
    assert response.status_code == 422


def test_create_book_duplicate_isbn(client, sample_book_data):
    """Test that creating book with duplicate ISBN is prevented."""
    from tests.conftest import get_auth_headers

    admin_headers = get_auth_headers(client, "admin@test.com", STRONG_PASSWORD, "admin")

    # Create first book
    response = client.post("/api/v1/books", json=sample_book_data, headers=admin_headers)
    assert response.status_code == 201

    # Try to create another book with same ISBN
    duplicate_data = sample_book_data.copy()
    duplicate_data["title"] = "Different Title"

    response = client.post("/api/v1/books", json=duplicate_data, headers=admin_headers)

    # Should return 409 Conflict or 400 Bad Request
    assert response.status_code in [400, 409]


def test_create_book_with_nonexistent_author(client):
    """Test creating book with non-existent author ID."""
    from tests.conftest import get_auth_headers

    admin_headers = get_auth_headers(client, "admin@test.com", STRONG_PASSWORD, "admin")

    book_data = {
        "title": "Book with Invalid Author",
        "isbn": "978-1-234567-89-0",
        "published_date": "2024-01-15",
        "description": "Test",
        "author_ids": [99999],  # Non-existent author
        "category_ids": []
    }

    response = client.post("/api/v1/books", json=book_data, headers=admin_headers)

    # Should return 400 or 404
    assert response.status_code in [400, 404]


def test_create_book_with_nonexistent_category(client):
    """Test creating book with non-existent category ID."""
    from tests.conftest import get_auth_headers

    admin_headers = get_auth_headers(client, "admin@test.com", STRONG_PASSWORD, "admin")

    book_data = {
        "title": "Book with Invalid Category",
        "isbn": "978-1-234567-89-0",
        "published_date": "2024-01-15",
        "description": "Test",
        "author_ids": [],
        "category_ids": [99999]  # Non-existent category
    }

    response = client.post("/api/v1/books", json=book_data, headers=admin_headers)

    # Should return 400 or 404
    assert response.status_code in [400, 404]


# ============================================================================
# TEST: UPDATE BOOK (PUT /api/v1/books/{id})
# ============================================================================

def test_update_book_as_admin_success(client, create_book):
    """Test that admin can update a book."""
    from tests.conftest import get_auth_headers

    admin_headers = get_auth_headers(client, "admin@test.com", STRONG_PASSWORD, is_admin=True)

    # Create book
    book = create_book(title="Original Title", isbn="978-1-111111-11-1")

    # Update book
    update_data = {
        "title": "Updated Title",
        "isbn": book["isbn"],  # Keep same ISBN
        "published_date": "2024-06-01",
        "description": "Updated description"
    }

    response = client.put(
        f"/api/v1/books/{book['id']}",
        json=update_data,
        headers=admin_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == book["id"]
    assert data["title"] == "Updated Title"
    assert data["description"] == "Updated description"


def test_update_book_partial_fields(client, create_book):
    """Test updating only specific fields of a book."""
    from tests.conftest import get_auth_headers

    admin_headers = get_auth_headers(client, "admin@test.com", STRONG_PASSWORD, is_admin=True)

    book = create_book(title="Original", isbn="978-1-111111-11-1")

    # Update only description
    update_data = {
        "description": "New description only"
    }

    response = client.put(
        f"/api/v1/books/{book['id']}",
        json=update_data,
        headers=admin_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Original"  # Title unchanged
    assert data["description"] == "New description only"


def test_update_book_as_user_forbidden(client, create_book):
    """Test that regular users cannot update books."""
    from tests.conftest import get_auth_headers

    user_headers = get_auth_headers(client, "user@test.com", STRONG_PASSWORD, is_admin=False)

    book = create_book(title="Test Book", isbn="978-1-111111-11-1")

    update_data = {"title": "Hacked Title"}

    response = client.put(
        f"/api/v1/books/{book['id']}",
        json=update_data,
        headers=user_headers
    )

    assert response.status_code == 403


def test_update_nonexistent_book(client):
    """Test updating non-existent book returns 404."""
    from tests.conftest import get_auth_headers

    admin_headers = get_auth_headers(client, "admin@test.com", STRONG_PASSWORD, is_admin=True)

    update_data = {"title": "Non-existent"}

    response = client.put(
        "/api/v1/books/99999",
        json=update_data,
        headers=admin_headers
    )

    assert response.status_code == 404


def test_update_book_without_auth(client, create_book):
    """Test updating book without authentication fails."""
    book = create_book(title="Test", isbn="978-1-111111-11-1")

    response = client.put(
        f"/api/v1/books/{book['id']}",
        json={"title": "Unauthorized Update"}
    )

    assert response.status_code == 401


# ============================================================================
# TEST: DELETE BOOK (DELETE /api/v1/books/{id})
# ============================================================================

def test_delete_book_as_admin_success(client, create_book):
    """Test that admin can delete a book."""
    from tests.conftest import get_auth_headers

    admin_headers = get_auth_headers(client, "admin@test.com", STRONG_PASSWORD, is_admin=True)

    book = create_book(title="To Delete", isbn="978-1-111111-11-1")

    # Delete book
    response = client.delete(f"/api/v1/books/{book['id']}", headers=admin_headers)

    assert response.status_code == 200  # API returns 200, not 204

    # Verify book is deleted
    get_response = client.get(f"/api/v1/books/{book['id']}")
    assert get_response.status_code == 404


def test_delete_book_as_user_forbidden(client, create_book):
    """Test that regular users cannot delete books."""
    from tests.conftest import get_auth_headers

    user_headers = get_auth_headers(client, "user@test.com", STRONG_PASSWORD, is_admin=False)

    book = create_book(title="Protected Book", isbn="978-1-111111-11-1")

    response = client.delete(f"/api/v1/books/{book['id']}", headers=user_headers)

    assert response.status_code == 403

    # Verify book still exists
    get_response = client.get(f"/api/v1/books/{book['id']}")
    assert get_response.status_code == 200


def test_delete_nonexistent_book(client):
    """Test deleting non-existent book returns 404."""
    from tests.conftest import get_auth_headers

    admin_headers = get_auth_headers(client, "admin@test.com", STRONG_PASSWORD, is_admin=True)

    response = client.delete("/api/v1/books/99999", headers=admin_headers)

    assert response.status_code == 404


def test_delete_book_without_auth(client, create_book):
    """Test deleting book without authentication fails."""
    book = create_book(title="Test", isbn="978-1-111111-11-1")

    response = client.delete(f"/api/v1/books/{book['id']}")

    assert response.status_code == 401


# ============================================================================
# TEST: EDGE CASES
# ============================================================================

def test_create_book_with_multiple_authors(client, create_author):
    """Test creating book with multiple authors."""
    from tests.conftest import get_auth_headers

    admin_headers = get_auth_headers(client, "admin@test.com", STRONG_PASSWORD, is_admin=True)

    # Create 3 authors
    author1 = create_author(name="Author One", headers=admin_headers)
    author2 = create_author(name="Author Two", headers=admin_headers)
    author3 = create_author(name="Author Three", headers=admin_headers)

    book_data = {
        "title": "Multi-Author Book",
        "isbn": "978-1-234567-89-0",
        "published_date": "2024-01-15",
        "description": "Book with multiple authors",
        "author_ids": [author1["id"], author2["id"], author3["id"]],
        "category_ids": []
    }

    response = client.post("/api/v1/books", json=book_data, headers=admin_headers)

    assert response.status_code == 201
    data = response.json()
    assert len(data["authors"]) == 3


def test_create_book_with_multiple_categories(client, create_category):
    """Test creating book with multiple categories."""
    from tests.conftest import get_auth_headers

    admin_headers = get_auth_headers(client, "admin@test.com", STRONG_PASSWORD, is_admin=True)

    # Create 3 categories
    cat1 = create_category(name="Fiction", headers=admin_headers)
    cat2 = create_category(name="Science", headers=admin_headers)
    cat3 = create_category(name="History", headers=admin_headers)

    book_data = {
        "title": "Multi-Category Book",
        "isbn": "978-1-234567-89-0",
        "published_date": "2024-01-15",
        "description": "Book with multiple categories",
        "author_ids": [],
        "category_ids": [cat1["id"], cat2["id"], cat3["id"]]
    }

    response = client.post("/api/v1/books", json=book_data, headers=admin_headers)

    assert response.status_code == 201
    data = response.json()
    assert len(data["categories"]) == 3


def test_list_books_with_combined_filters(client, create_book, create_author, create_category):
    """Test listing books with multiple filters combined."""
    from tests.conftest import get_auth_headers

    admin_headers = get_auth_headers(client, "admin@test.com", STRONG_PASSWORD, is_admin=True)

    # Create author and category
    author = create_author(name="Specific Author", headers=admin_headers)
    category = create_category(name="Specific Category", headers=admin_headers)

    # Create book with both
    book_data = {
        "title": "Filtered Book",
        "isbn": "978-1-234567-89-0",
        "published_date": "2024-01-15",
        "description": "Test",
        "author_ids": [author["id"]],
        "category_ids": [category["id"]]
    }
    client.post("/api/v1/books", json=book_data, headers=admin_headers)

    # Filter by both author and category
    response = client.get(
        f"/api/v1/books?author_id={author['id']}&category={category['name']}"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
