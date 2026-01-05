"""
Unit tests for database exception handling.

These tests verify that database errors are properly caught and handled,
returning appropriate HTTP status codes and user-friendly error messages.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, OperationalError
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import date
from tests.conftest import get_auth_headers, STRONG_PASSWORD


class TestIntegrityErrorHandling:
    """Test handling of database integrity errors."""

    def test_create_book_duplicate_isbn_precheck(self, client):
        """Test that duplicate ISBN is caught by database constraint."""
        auth_headers = get_auth_headers(client, "author1@example.com", STRONG_PASSWORD)
        book_data = {
            "title": "Test Book",
            "author": "Test Author",
            "isbn": "978-1111111111",
            "published_date": "2023-01-15",
            "description": "Test description"
        }

        # Create first book
        response1 = client.post("/api/v1/books", json=book_data, headers=auth_headers)
        assert response1.status_code == 201

        # Try to create duplicate - should fail at database constraint
        response2 = client.post("/api/v1/books", json=book_data, headers=auth_headers)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"].lower()

    def test_create_book_integrity_error_race_condition(self, client):
        """Test IntegrityError during commit is handled (simulates race condition)."""
        auth_headers = get_auth_headers(client, "author2@example.com", STRONG_PASSWORD)
        book_data = {
            "title": "Race Condition Book",
            "author": "Test Author",
            "isbn": "978-9999999999",
            "published_date": "2023-01-15",
            "description": "Test"
        }

        # Mock the commit to raise IntegrityError
        with patch('sqlalchemy.orm.Session.commit') as mock_commit:
            # Create mock original exception
            mock_orig = MagicMock()
            mock_orig.__str__ = MagicMock(return_value="duplicate key value violates unique constraint books_isbn_key")

            # Create IntegrityError with the mock
            integrity_error = IntegrityError("statement", "params", mock_orig)
            mock_commit.side_effect = integrity_error

            response = client.post("/api/v1/books", json=book_data, headers=auth_headers)

            # Should return 400 Bad Request (consistent with constraint violations)
            assert response.status_code == 400
            assert "isbn" in response.json()["detail"].lower() or "exists" in response.json()["detail"].lower()

    def test_update_book_duplicate_isbn_integrity_error(self, client):
        """Test that duplicate ISBN during update is handled."""
        auth_headers = get_auth_headers(client, "author3@example.com", STRONG_PASSWORD)
        # Create two books
        book1_data = {
            "title": "Book 1",
            "author": "Author 1",
            "isbn": "978-1111111112",
            "published_date": "2023-01-15",
        }
        book2_data = {
            "title": "Book 2",
            "author": "Author 2",
            "isbn": "978-2222222222",
            "published_date": "2023-01-15",
        }

        response1 = client.post("/api/v1/books", json=book1_data, headers=auth_headers)
        response2 = client.post("/api/v1/books", json=book2_data, headers=auth_headers)

        book2_id = response2.json()["id"]

        # Try to update book2 with book1's ISBN
        update_data = {"isbn": "978-1111111112"}
        response = client.put(f"/api/v1/books/{book2_id}", json=update_data, headers=auth_headers)

        assert response.status_code == 400
        assert "exists" in response.json()["detail"].lower()


class TestDatabaseErrorHandling:
    """Test handling of general database errors."""

    def test_create_book_database_error(self, client):
        """Test that generic database errors return 500."""
        auth_headers = get_auth_headers(client, "author4@example.com", STRONG_PASSWORD)
        book_data = {
            "title": "Test Book",
            "author": "Test Author",
            "isbn": "978-8888888888",
            "published_date": "2023-01-15",
        }

        # Mock commit to raise a generic SQLAlchemyError
        with patch('sqlalchemy.orm.Session.commit') as mock_commit:
            from sqlalchemy.exc import DatabaseError
            mock_commit.side_effect = DatabaseError("statement", "params", "database connection lost")

            response = client.post("/api/v1/books", json=book_data, headers=auth_headers)

            # Should return 500 Internal Server Error
            assert response.status_code == 500
            assert "error occurred" in response.json()["detail"].lower()

    def test_get_books_database_error(self, client):
        """Test that database errors during query are handled."""
        with patch('sqlalchemy.orm.Query.all') as mock_all:
            mock_all.side_effect = SQLAlchemyError("Database error")

            response = client.get("/api/v1/books")

            assert response.status_code == 500
            assert "error occurred" in response.json()["detail"].lower()


class TestDeleteConstraints:
    """Test handling of delete operations with constraints."""

    def test_delete_book_foreign_key_constraint(self, client):
        """Test that foreign key constraint violations are handled properly."""
        auth_headers = get_auth_headers(client, "author5@example.com", STRONG_PASSWORD)
        admin_headers = get_auth_headers(client, "admin@example.com", STRONG_PASSWORD, role="admin")
        
        # Create a book
        book_data = {
            "title": "Book with References",
            "author": "Author",
            "isbn": "978-5555555555",
            "published_date": "2023-01-15",
        }
        create_response = client.post("/api/v1/books", json=book_data, headers=auth_headers)
        book_id = create_response.json()["id"]

        # Mock the commit to simulate foreign key constraint error
        with patch('sqlalchemy.orm.Session.commit') as mock_commit:
            mock_orig = MagicMock()
            mock_orig.__str__ = MagicMock(return_value="foreign key constraint fails")

            integrity_error = IntegrityError("statement", "params", mock_orig)
            mock_commit.side_effect = integrity_error

            response = client.delete(f"/api/v1/books/{book_id}", headers=admin_headers)

            # Should return 409 Conflict
            assert response.status_code == 409
            assert "referenced" in response.json()["detail"].lower() or "constraint" in response.json()["detail"].lower()

    def test_delete_nonexistent_book(self, client):
        """Test deleting a book that doesn't exist returns 404."""
        admin_headers = get_auth_headers(client, "admin2@example.com", STRONG_PASSWORD, role="admin")
        response = client.delete("/api/v1/books/99999", headers=admin_headers)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestConcurrentOperations:
    """Test handling of concurrent database operations."""

    def test_concurrent_create_same_isbn(self, client):
        """Test that concurrent creates with same ISBN are handled."""
        auth_headers = get_auth_headers(client, "author6@example.com", STRONG_PASSWORD)
        book_data = {
            "title": "Concurrent Book",
            "author": "Author",
            "isbn": "978-4444444444",
            "published_date": "2023-01-15",
        }

        # First request succeeds
        response1 = client.post("/api/v1/books", json=book_data, headers=auth_headers)
        assert response1.status_code == 201

        # Second request should fail
        response2 = client.post("/api/v1/books", json=book_data, headers=auth_headers)
        assert response2.status_code in [400, 409]
        assert "exists" in response2.json()["detail"].lower()


class TestErrorResponses:
    """Test that error responses have correct structure."""

    def test_error_response_structure(self, client):
        """Test that error responses include expected fields."""
        auth_headers = get_auth_headers(client, "author7@example.com", STRONG_PASSWORD)
        book_data = {
            "title": "Test Book",
            "author": "Test Author",
            "isbn": "978-6666666666",
            "published_date": "2023-01-15",
        }

        # Create book
        client.post("/api/v1/books", json=book_data, headers=auth_headers)

        # Try to create duplicate
        response = client.post("/api/v1/books", json=book_data, headers=auth_headers)

        assert response.status_code in [400, 409]
        response_data = response.json()

        # Should have 'detail' field
        assert "detail" in response_data
        assert isinstance(response_data["detail"], str)
        assert len(response_data["detail"]) > 0

    def test_404_error_structure(self, client):
        """Test that 404 errors have correct structure."""
        response = client.get("/api/v1/books/99999")

        assert response.status_code == 404
        response_data = response.json()

        assert "detail" in response_data
        assert "not found" in response_data["detail"].lower()


class TestRollbackBehavior:
    """Test that failed operations properly roll back."""

    def test_failed_create_rolls_back(self, client):
        """Test that a failed create operation doesn't leave partial data."""
        auth_headers = get_auth_headers(client, "author8@example.com", STRONG_PASSWORD)
        book_data = {
            "title": "Rollback Test Book",
            "author": "Test Author",
            "isbn": "978-7777777777",
            "published_date": "2023-01-15",
        }

        # Create book successfully
        response1 = client.post("/api/v1/books", json=book_data, headers=auth_headers)
        assert response1.status_code == 201
        book_id = response1.json()["id"]

        # Try to create duplicate (should fail and rollback)
        response2 = client.post("/api/v1/books", json=book_data, headers=auth_headers)
        assert response2.status_code in [400, 409]

        # Verify only one book exists with this ID (the first one)
        response = client.get(f"/api/v1/books/{book_id}")
        assert response.status_code == 200

        # Verify it has the original data (ISBN is normalized to remove dashes)
        book = response.json()
        assert book["isbn"] == "9787777777777"  # Normalized ISBN
        assert book["title"] == book_data["title"]


class TestGetOperationsErrorHandling:
    """Test error handling for GET operations."""

    def test_get_book_by_id_not_found(self, client):
        """Test getting a non-existent book returns 404."""
        response = client.get("/api/v1/books/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_book_database_error(self, client):
        """Test that database errors during single book retrieval are handled."""
        auth_headers = get_auth_headers(client, "author9@example.com", STRONG_PASSWORD)
        # Create a book first
        book_data = {
            "title": "Test Book for Error",
            "author": "Test Author",
            "isbn": "978-3333333333",
            "published_date": "2023-01-15",
        }
        create_response = client.post("/api/v1/books", json=book_data, headers=auth_headers)
        book_id = create_response.json()["id"]

        # Mock the query to raise an error
        with patch('sqlalchemy.orm.Query.first') as mock_first:
            mock_first.side_effect = SQLAlchemyError("Database error")

            response = client.get(f"/api/v1/books/{book_id}")

            assert response.status_code == 500
            assert "error occurred" in response.json()["detail"].lower()


class TestUpdateOperationsErrorHandling:
    """Test error handling for UPDATE operations."""

    def test_update_book_not_found(self, client):
        """Test updating a non-existent book returns 404."""
        auth_headers = get_auth_headers(client, "author10@example.com", STRONG_PASSWORD)
        update_data = {"title": "Updated Title"}
        response = client.put("/api/v1/books/99999", json=update_data, headers=auth_headers)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_book_database_error(self, client):
        """Test that database errors during update are handled."""
        auth_headers = get_auth_headers(client, "author11@example.com", STRONG_PASSWORD)
        # Create a book
        book_data = {
            "title": "Original Title",
            "author": "Author",
            "isbn": "978-1234567890",
            "published_date": "2023-01-15",
        }
        create_response = client.post("/api/v1/books", json=book_data, headers=auth_headers)
        book_id = create_response.json()["id"]

        # Mock commit to raise error
        with patch('sqlalchemy.orm.Session.commit') as mock_commit:
            from sqlalchemy.exc import DatabaseError
            mock_commit.side_effect = DatabaseError("statement", "params", "connection error")

            update_data = {"title": "New Title"}
            response = client.put(f"/api/v1/books/{book_id}", json=update_data, headers=auth_headers)

            assert response.status_code == 500
            assert "error occurred" in response.json()["detail"].lower()

