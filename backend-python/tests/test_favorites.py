"""
TDD Tests for Favorites Feature.

These tests are written FIRST before implementation (TDD approach).
They will fail until we implement the favorites feature.
"""
import pytest
from datetime import datetime, timezone
from tests.conftest import get_auth_headers, create_test_author, create_test_book, STRONG_PASSWORD


class TestFavoriteSchemas:
    """Test suite for favorite Pydantic schemas."""

    def test_favorite_response_schema(self):
        """Test FavoriteResponse schema instantiation."""
        from src.schemas.favorite import FavoriteResponse

        favorite = FavoriteResponse(
            id=1,
            user_id=1,
            book_id=1,
            created_at=datetime.now(timezone.utc)
        )
        assert favorite.id == 1
        assert favorite.user_id == 1
        assert favorite.book_id == 1
        assert favorite.created_at is not None

    def test_favorite_book_response_schema(self):
        """Test FavoriteBookResponse schema instantiation."""
        from src.schemas.favorite import FavoriteBookResponse

        book = FavoriteBookResponse(
            id=1,
            title="Test Book",
            isbn="9781234567890",
            published_date="2023-01-15",
            description="A test book"
        )
        assert book.id == 1
        assert book.title == "Test Book"
        assert book.isbn == "9781234567890"
        assert book.published_date == "2023-01-15"
        assert book.description == "A test book"

    def test_favorite_book_response_schema_no_description(self):
        """Test FavoriteBookResponse schema with no description."""
        from src.schemas.favorite import FavoriteBookResponse

        book = FavoriteBookResponse(
            id=1,
            title="Test Book",
            isbn="9781234567890",
            published_date="2023-01-15"
        )
        assert book.description is None

    def test_favorite_with_book_response_schema(self):
        """Test FavoriteWithBookResponse schema instantiation."""
        from src.schemas.favorite import FavoriteWithBookResponse, FavoriteBookResponse

        book_data = FavoriteBookResponse(
            id=1,
            title="Test Book",
            isbn="9781234567890",
            published_date="2023-01-15",
            description="A test book"
        )
        favorite = FavoriteWithBookResponse(
            id=1,
            book_id=1,
            created_at=datetime.now(timezone.utc),
            book=book_data
        )
        assert favorite.id == 1
        assert favorite.book_id == 1
        assert favorite.book.title == "Test Book"


class TestFavorites:
    """Test suite for favorites functionality."""

    def test_add_favorite(self, client):
        """User can favorite a book."""
        admin_headers = get_auth_headers(client, "fav_admin@example.com", STRONG_PASSWORD, is_admin=True)
        user_headers = get_auth_headers(client, "fav_user@example.com", STRONG_PASSWORD)

        # Create a book
        author = create_test_author(client, "Favorite Author", admin_headers=admin_headers)
        book = create_test_book(
            client,
            title="Favorite Book",
            isbn="978-0-111-11111-1",
            author_ids=[author["id"]],
            admin_headers=admin_headers
        )

        # Add book to favorites
        response = client.post(
            f"/api/v1/books/{book['id']}/favorite",
            headers=user_headers
        )
        assert response.status_code == 201

        data = response.json()
        assert "message" in data or "id" in data

    def test_remove_favorite(self, client):
        """User can unfavorite a book."""
        admin_headers = get_auth_headers(client, "unfav_admin@example.com", STRONG_PASSWORD, is_admin=True)
        user_headers = get_auth_headers(client, "unfav_user@example.com", STRONG_PASSWORD)

        # Create a book
        author = create_test_author(client, "Unfavorite Author", admin_headers=admin_headers)
        book = create_test_book(
            client,
            title="Unfavorite Book",
            isbn="978-0-222-22222-2",
            author_ids=[author["id"]],
            admin_headers=admin_headers
        )

        # Add to favorites first
        client.post(f"/api/v1/books/{book['id']}/favorite", headers=user_headers)

        # Remove from favorites
        response = client.delete(
            f"/api/v1/books/{book['id']}/favorite",
            headers=user_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert "message" in data

    def test_list_favorites(self, client):
        """User can list their favorites."""
        admin_headers = get_auth_headers(client, "list_admin@example.com", STRONG_PASSWORD, is_admin=True)
        user_headers = get_auth_headers(client, "list_user@example.com", STRONG_PASSWORD)

        # Create multiple books
        author = create_test_author(client, "List Author", admin_headers=admin_headers)
        books = []
        for i in range(3):
            book = create_test_book(
                client,
                title=f"List Book {i}",
                isbn=f"978-0-333-3333{i}-{i}",
                author_ids=[author["id"]],
                admin_headers=admin_headers
            )
            books.append(book)

        # Favorite first 2 books
        for book in books[:2]:
            client.post(f"/api/v1/books/{book['id']}/favorite", headers=user_headers)

        # List favorites
        response = client.get("/api/v1/users/me/favorites", headers=user_headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

    def test_duplicate_favorite_fails(self, client):
        """Can't favorite same book twice."""
        admin_headers = get_auth_headers(client, "dup_admin@example.com", STRONG_PASSWORD, is_admin=True)
        user_headers = get_auth_headers(client, "dup_user@example.com", STRONG_PASSWORD)

        # Create a book
        author = create_test_author(client, "Duplicate Author", admin_headers=admin_headers)
        book = create_test_book(
            client,
            title="Duplicate Book",
            isbn="978-0-444-44444-4",
            author_ids=[author["id"]],
            admin_headers=admin_headers
        )

        # Add to favorites
        response1 = client.post(f"/api/v1/books/{book['id']}/favorite", headers=user_headers)
        assert response1.status_code == 201

        # Try to add again
        response2 = client.post(
            f"/api/v1/books/{book['id']}/favorite",
            headers=user_headers
        )
        assert response2.status_code == 400
        assert "already" in response2.json()["detail"].lower()

    def test_favorite_requires_auth(self, client):
        """Must be authenticated to favorite."""
        admin_headers = get_auth_headers(client, "auth_admin@example.com", STRONG_PASSWORD, is_admin=True)

        # Create a book
        author = create_test_author(client, "Auth Author", admin_headers=admin_headers)
        book = create_test_book(
            client,
            title="Auth Book",
            isbn="978-0-555-55555-5",
            author_ids=[author["id"]],
            admin_headers=admin_headers
        )

        # Try to favorite without authentication
        response = client.post(f"/api/v1/books/{book['id']}/favorite")
        assert response.status_code == 401

    def test_favorite_nonexistent_book(self, client):
        """Cannot favorite a book that doesn't exist."""
        user_headers = get_auth_headers(client, "nobook_user@example.com", STRONG_PASSWORD)

        response = client.post("/api/v1/books/99999/favorite", headers=user_headers)
        assert response.status_code == 404

    def test_unfavorite_not_favorited_book(self, client):
        """Unfavoriting a book that isn't favorited returns 404."""
        admin_headers = get_auth_headers(client, "notfav_admin@example.com", STRONG_PASSWORD, is_admin=True)
        user_headers = get_auth_headers(client, "notfav_user@example.com", STRONG_PASSWORD)

        # Create a book but don't favorite it
        author = create_test_author(client, "NotFav Author", admin_headers=admin_headers)
        book = create_test_book(
            client,
            title="NotFav Book",
            isbn="978-0-666-66666-6",
            author_ids=[author["id"]],
            admin_headers=admin_headers
        )

        # Try to unfavorite
        response = client.delete(f"/api/v1/books/{book['id']}/favorite", headers=user_headers)
        assert response.status_code == 404

    def test_favorites_isolated_per_user(self, client):
        """Each user has their own favorites list."""
        admin_headers = get_auth_headers(client, "iso_admin@example.com", STRONG_PASSWORD, is_admin=True)
        user1_headers = get_auth_headers(client, "iso_user1@example.com", STRONG_PASSWORD)
        user2_headers = get_auth_headers(client, "iso_user2@example.com", STRONG_PASSWORD)

        # Create a book
        author = create_test_author(client, "Isolation Author", admin_headers=admin_headers)
        book = create_test_book(
            client,
            title="Isolation Book",
            isbn="978-0-777-77777-7",
            author_ids=[author["id"]],
            admin_headers=admin_headers
        )

        # User 1 favorites the book
        client.post(f"/api/v1/books/{book['id']}/favorite", headers=user1_headers)

        # User 1 should see it in favorites
        response1 = client.get("/api/v1/users/me/favorites", headers=user1_headers)
        assert len(response1.json()) == 1

        # User 2 should NOT see it in their favorites
        response2 = client.get("/api/v1/users/me/favorites", headers=user2_headers)
        assert len(response2.json()) == 0

    def test_list_favorites_requires_auth(self, client):
        """Must be authenticated to list favorites."""
        response = client.get("/api/v1/users/me/favorites")
        assert response.status_code == 401

    def test_unfavorite_requires_auth(self, client):
        """Must be authenticated to unfavorite."""
        response = client.delete("/api/v1/books/1/favorite")
        assert response.status_code == 401

    def test_favorite_response_contains_book_details(self, client):
        """Favorites list returns book details."""
        admin_headers = get_auth_headers(client, "details_admin@example.com", STRONG_PASSWORD, is_admin=True)
        user_headers = get_auth_headers(client, "details_user@example.com", STRONG_PASSWORD)

        # Create a book with all details
        author = create_test_author(client, "Details Author", admin_headers=admin_headers)
        book = create_test_book(
            client,
            title="Details Book",
            isbn="978-0-888-88888-8",
            author_ids=[author["id"]],
            description="A detailed description",
            admin_headers=admin_headers
        )

        # Add to favorites
        client.post(f"/api/v1/books/{book['id']}/favorite", headers=user_headers)

        # List favorites and verify book details are present
        response = client.get("/api/v1/users/me/favorites", headers=user_headers)
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Details Book"
        assert "isbn" in data[0]
        assert "description" in data[0]
