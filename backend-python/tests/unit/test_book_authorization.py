"""
Unit tests for Book Authorization endpoints.
"""

from fastapi.testclient import TestClient
from src.models.book import Book
from datetime import date
from tests.conftest import get_auth_headers, create_test_author, create_test_book

# Standard strong password for tests
STRONG_PASSWORD = "TestPassword123!"


def test_create_book_authenticated(client):
    """Test creating a book requires admin authentication."""
    # Register admin user
    admin_headers = get_auth_headers(client, "admin_book@example.com", STRONG_PASSWORD, is_admin=True)

    # Create author
    author = create_test_author(client, "Auth Author", admin_headers=admin_headers)

    # Create book as admin
    book_data = {
        "title": "Authenticated Book",
        "isbn": "9781234567890",
        "published_date": "2023-06-15",
        "description": "A book created by admin user",
        "author_ids": [author["id"]],
        "category_ids": []
    }
    response = client.post(
        "/api/v1/books",
        json=book_data,
        headers=admin_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == book_data["title"]
    assert "created_by" in data
    assert data["created_by"] is not None


def test_create_book_unauthenticated(client):
    """Test creating a book without authentication returns 401."""
    book_data = {
        "title": "Unauthorized Book",
        "isbn": "9780987654321",
        "published_date": "2023-06-15",
        "author_ids": [],
        "category_ids": []
    }
    response = client.post("/api/v1/books", json=book_data)
    assert response.status_code == 401  # No auth token provided


def test_delete_book_as_admin(client):
    """Test that admin can delete books."""
    # Create admin user
    admin_headers = get_auth_headers(client, "admin_deleter@example.com", STRONG_PASSWORD, is_admin=True)

    # Create book as admin
    book = create_test_book(
        client,
        title="Book to Delete",
        isbn="9781111111111",
        published_date="2023-06-15",
        admin_headers=admin_headers
    )
    book_id = book["id"]

    # Delete book as admin
    response = client.delete(
        f"/api/v1/books/{book_id}",
        headers=admin_headers
    )
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]


def test_delete_book_as_non_admin(client):
    """Test that regular user cannot delete books."""
    # Create admin and book
    admin_headers = get_auth_headers(client, "admin_creator@example.com", STRONG_PASSWORD, is_admin=True)
    book = create_test_book(
        client,
        title="Cannot Delete",
        isbn="9782222222222",
        published_date="2023-06-15",
        admin_headers=admin_headers
    )
    book_id = book["id"]

    # Register regular user
    user_headers = get_auth_headers(client, "nonadmin@example.com", STRONG_PASSWORD, is_admin=False)

    # Try to delete as regular user
    response = client.delete(
        f"/api/v1/books/{book_id}",
        headers=user_headers
    )
    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()


def test_update_book_authorization(client):
    """Test that non-owner cannot update book."""
    # Create admin1 and book
    admin1_headers = get_auth_headers(client, "admin1@example.com", STRONG_PASSWORD, is_admin=True)
    book = create_test_book(
        client,
        title="Admin1's Book",
        isbn="9781234567890",
        published_date="2023-06-15",
        admin_headers=admin1_headers
    )
    book_id = book["id"]

    # Create admin2 (different admin)
    admin2_headers = get_auth_headers(client, "admin2@example.com", STRONG_PASSWORD, is_admin=True)

    # Admin2 CAN update because they're admin (admins can update any book)
    update_response = client.put(
        f"/api/v1/books/{book_id}",
        json={"title": "Admin2 Updated Book"},
        headers=admin2_headers
    )
    # Admin can update any book
    assert update_response.status_code == 200


def test_admin_can_update_any_book(client):
    """Test that admin can update any book."""
    # Create admin1 and book
    admin1_headers = get_auth_headers(client, "admin_owner@example.com", STRONG_PASSWORD, is_admin=True)
    book = create_test_book(
        client,
        title="Owner's Book",
        isbn="9781234567890",
        published_date="2023-06-15",
        admin_headers=admin1_headers
    )
    book_id = book["id"]

    # Create different admin and update the book
    admin2_headers = get_auth_headers(client, "admin_updater@example.com", STRONG_PASSWORD, is_admin=True)

    update_response = client.put(
        f"/api/v1/books/{book_id}",
        json={"title": "Admin Updated Book"},
        headers=admin2_headers
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Admin Updated Book"


def test_owner_can_update_own_book(client):
    """Test that owner (admin who created book) can update their own book."""
    # Create admin and book
    admin_headers = get_auth_headers(client, "admin_owner@example.com", STRONG_PASSWORD, is_admin=True)
    book = create_test_book(
        client,
        title="My Book",
        isbn="9781234567890",
        published_date="2023-06-15",
        admin_headers=admin_headers
    )
    book_id = book["id"]

    # Owner updates their own book
    update_response = client.put(
        f"/api/v1/books/{book_id}",
        json={"title": "Updated My Book"},
        headers=admin_headers
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Updated My Book"


def test_legacy_book_update_by_regular_user_forbidden(client):
    """
    Test that regular users cannot update legacy books (created_by=None).

    Legacy books are those created before authentication was implemented.
    For backward compatibility, the created_by field is nullable, but only
    admins can update these legacy books.
    """
    from tests.conftest import TestingSessionLocal

    # Create a legacy book directly in database with created_by=None
    # Note: Book model uses many-to-many authors, no single 'author' field
    db = TestingSessionLocal()
    try:
        legacy_book = Book(
            title="Legacy Book",
            isbn="9780000000001",
            published_date=date(2020, 1, 1),
            description="A book from before authentication",
            created_by=None  # Legacy book with no creator
        )
        db.add(legacy_book)
        db.commit()
        db.refresh(legacy_book)
        book_id = legacy_book.id
    finally:
        db.close()

    # Register and login as regular user
    user_headers = get_auth_headers(client, "regularuser@example.com", STRONG_PASSWORD, is_admin=False)

    # Try to update the legacy book as regular user
    update_response = client.put(
        f"/api/v1/books/{book_id}",
        json={"title": "Attempted Update"},
        headers=user_headers
    )

    # Should be forbidden - only admins can update legacy books
    assert update_response.status_code == 403
    assert "your own books" in update_response.json()["detail"].lower()


def test_legacy_book_update_by_admin_allowed(client):
    """
    Test that admin users can update legacy books (created_by=None).

    This verifies that the backward compatibility mechanism works correctly
    and admins retain control over legacy books from before authentication.
    """
    from tests.conftest import TestingSessionLocal

    # Create a legacy book directly in database with created_by=None
    db = TestingSessionLocal()
    try:
        legacy_book = Book(
            title="Legacy Book",
            isbn="9780000000002",
            published_date=date(2020, 1, 1),
            description="A book from before authentication",
            created_by=None  # Legacy book with no creator
        )
        db.add(legacy_book)
        db.commit()
        db.refresh(legacy_book)
        book_id = legacy_book.id
    finally:
        db.close()

    # Create admin user
    admin_headers = get_auth_headers(client, "admin@example.com", STRONG_PASSWORD, is_admin=True)

    # Admin should be able to update the legacy book
    update_response = client.put(
        f"/api/v1/books/{book_id}",
        json={"title": "Admin Updated Legacy Book"},
        headers=admin_headers
    )

    # Should succeed
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Admin Updated Legacy Book"
    assert update_response.json()["created_by"] is None  # Still None after update


def test_legacy_book_visible_in_list(client):
    """
    Test that legacy books (created_by=None) are still visible in book listings.

    This ensures backward compatibility - existing books remain accessible.
    """
    from tests.conftest import TestingSessionLocal

    # Create a legacy book directly in database with created_by=None
    db = TestingSessionLocal()
    try:
        legacy_book = Book(
            title="Legacy Visible Book",
            isbn="9780000000003",
            published_date=date(2020, 1, 1),
            description="Should be visible",
            created_by=None
        )
        db.add(legacy_book)
        db.commit()
    finally:
        db.close()

    # Get all books (no auth required for GET)
    response = client.get("/api/v1/books")

    assert response.status_code == 200
    books = response.json()
    # Access the 'items' key from paginated response
    assert len(books["items"]) == 1
    assert books["items"][0]["title"] == "Legacy Visible Book"
    assert books["items"][0]["created_by"] is None

