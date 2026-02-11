"""
Additional tests for Authors endpoints to increase coverage.
Covers error handling paths and edge cases.
"""
import pytest
from tests.conftest import (
    get_auth_headers, create_test_author, create_test_book,
    STRONG_PASSWORD
)


class TestAuthorsEdgeCases:
    """Test edge cases and error handling in authors endpoints."""

    def test_get_authors_empty_list(self, client):
        """Test getting authors when none exist."""
        response = client.get("/api/v1/authors")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_author_not_found(self, client):
        """Test getting a non-existent author."""
        response = client.get("/api/v1/authors/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_update_author_not_found(self, client):
        """Test updating a non-existent author."""
        auth_headers = get_auth_headers(client, "auth_upd_nf@example.com", STRONG_PASSWORD, is_admin=True)

        response = client.put(
            "/api/v1/authors/99999",
            json={"name": "Updated Name"},
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_delete_author_not_found(self, client):
        """Test deleting a non-existent author."""
        auth_headers = get_auth_headers(client, "auth_del_nf@example.com", STRONG_PASSWORD, is_admin=True)

        response = client.delete("/api/v1/authors/99999", headers=auth_headers)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_delete_author_with_books(self, client):
        """Test that authors with books cannot be deleted."""
        auth_headers = get_auth_headers(client, "auth_del_books@example.com", STRONG_PASSWORD, is_admin=True)

        # Create author
        author = create_test_author(client, "Author With Books", admin_headers=auth_headers)

        # Create a book for this author
        book = create_test_book(
            client,
            title="Author's Book",
            isbn="9782222222222",
            author_ids=[author["id"]],
            admin_headers=auth_headers
        )

        # Try to delete author
        response = client.delete(f"/api/v1/authors/{author['id']}", headers=auth_headers)

        assert response.status_code == 409
        assert "book(s)" in response.json()["detail"]

    def test_delete_author_success(self, client):
        """Test successfully deleting an author without books."""
        auth_headers = get_auth_headers(client, "auth_del_ok@example.com", STRONG_PASSWORD, is_admin=True)

        # Create author without books
        author = create_test_author(client, "Author To Delete", admin_headers=auth_headers)

        # Delete author
        response = client.delete(f"/api/v1/authors/{author['id']}", headers=auth_headers)

        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        # Verify deletion
        get_response = client.get(f"/api/v1/authors/{author['id']}")
        assert get_response.status_code == 404

    def test_update_author_partial(self, client):
        """Test partial update of an author."""
        auth_headers = get_auth_headers(client, "auth_part@example.com", STRONG_PASSWORD, is_admin=True)

        # Create author with full details
        author = create_test_author(
            client,
            "Full Author",
            bio="Original bio",
            nationality="American",
            admin_headers=auth_headers
        )

        # Update only bio
        response = client.put(
            f"/api/v1/authors/{author['id']}",
            json={"bio": "Updated bio"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Full Author"  # Unchanged
        assert data["bio"] == "Updated bio"
        assert data["nationality"] == "American"  # Unchanged

    def test_get_author_with_books(self, client):
        """Test getting an author includes their books."""
        auth_headers = get_auth_headers(client, "auth_books@example.com", STRONG_PASSWORD, is_admin=True)

        # Create author
        author = create_test_author(client, "Author With Multiple Books", admin_headers=auth_headers)

        # Create multiple books
        for i in range(3):
            create_test_book(
                client,
                title=f"Book {i+1}",
                isbn=f"978333333333{i}",
                author_ids=[author["id"]],
                admin_headers=auth_headers
            )

        # Get author
        response = client.get(f"/api/v1/authors/{author['id']}")

        assert response.status_code == 200
        data = response.json()
        assert "books" in data
        assert len(data["books"]) == 3

    def test_create_author_with_all_fields(self, client):
        """Test creating an author with all optional fields."""
        auth_headers = get_auth_headers(client, "auth_full@example.com", STRONG_PASSWORD, is_admin=True)

        author_data = {
            "name": "Complete Author",
            "bio": "A detailed biography of the author",
            "birth_date": "1990-05-15",
            "nationality": "British"
        }

        response = client.post("/api/v1/authors", json=author_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Complete Author"
        assert data["bio"] == "A detailed biography of the author"
        assert data["birth_date"] == "1990-05-15"
        assert data["nationality"] == "British"

    def test_create_author_requires_admin(self, client):
        """Test that only admins can create authors."""
        user_headers = get_auth_headers(client, "auth_user@example.com", STRONG_PASSWORD)

        author_data = {"name": "User Created Author"}

        response = client.post("/api/v1/authors", json=author_data, headers=user_headers)

        assert response.status_code == 403

    def test_update_author_requires_admin(self, client):
        """Test that only admins can update authors."""
        admin_headers = get_auth_headers(client, "auth_admin_upd@example.com", STRONG_PASSWORD, is_admin=True)
        user_headers = get_auth_headers(client, "auth_user_upd@example.com", STRONG_PASSWORD)

        # Create author with admin
        author = create_test_author(client, "Admin Created Author", admin_headers=admin_headers)

        # Try to update with regular user
        response = client.put(
            f"/api/v1/authors/{author['id']}",
            json={"name": "User Updated"},
            headers=user_headers
        )

        assert response.status_code == 403

    def test_delete_author_requires_admin(self, client):
        """Test that only admins can delete authors."""
        admin_headers = get_auth_headers(client, "auth_admin_del@example.com", STRONG_PASSWORD, is_admin=True)
        user_headers = get_auth_headers(client, "auth_user_del@example.com", STRONG_PASSWORD)

        # Create author with admin
        author = create_test_author(client, "Admin Only Delete Author", admin_headers=admin_headers)

        # Try to delete with regular user
        response = client.delete(f"/api/v1/authors/{author['id']}", headers=user_headers)

        assert response.status_code == 403


class TestAuthorsValidation:
    """Test validation rules for authors."""

    def test_create_author_requires_auth(self, client):
        """Test that creating an author requires authentication."""
        author_data = {"name": "No Auth Author"}

        response = client.post("/api/v1/authors", json=author_data)

        assert response.status_code == 401

    def test_update_author_requires_auth(self, client):
        """Test that updating an author requires authentication."""
        response = client.put("/api/v1/authors/1", json={"name": "Updated"})

        assert response.status_code == 401

    def test_delete_author_requires_auth(self, client):
        """Test that deleting an author requires authentication."""
        response = client.delete("/api/v1/authors/1")

        assert response.status_code == 401

    def test_create_author_missing_name(self, client):
        """Test that author name is required."""
        auth_headers = get_auth_headers(client, "auth_no_name@example.com", STRONG_PASSWORD, is_admin=True)

        response = client.post("/api/v1/authors", json={}, headers=auth_headers)

        assert response.status_code == 422  # Validation error

