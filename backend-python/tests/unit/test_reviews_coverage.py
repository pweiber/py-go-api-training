"""
Additional tests for Reviews endpoints to increase coverage.
Covers error handling paths and edge cases.
"""
import pytest
from tests.conftest import (
    get_auth_headers, create_test_author, create_test_book,
    create_test_category, STRONG_PASSWORD
)


class TestReviewsEdgeCases:
    """Test edge cases and error handling in reviews endpoints."""

    def test_create_review_book_not_found(self, client):
        """Test creating a review for non-existent book."""
        user_headers = get_auth_headers(client, "rev_no_book@example.com", STRONG_PASSWORD)

        review_data = {
            "book_id": 99999,
            "rating": 5,
            "comment": "Great book!"
        }

        response = client.post("/api/v1/reviews", json=review_data, headers=user_headers)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_create_review_own_book(self, client):
        """Test that users cannot review their own books."""
        # User creates a book (need admin to create book)
        admin_headers = get_auth_headers(client, "rev_own_admin@example.com", STRONG_PASSWORD, is_admin=True)

        # Create author and book
        author = create_test_author(client, "Self Review Author", admin_headers=admin_headers)
        book = create_test_book(
            client,
            title="My Own Book",
            isbn="9781111111111",
            author_ids=[author["id"]],
            admin_headers=admin_headers
        )

        # Admin tries to review their own book
        review_data = {
            "book_id": book["id"],
            "rating": 5,
            "comment": "My book is awesome!"
        }

        response = client.post("/api/v1/reviews", json=review_data, headers=admin_headers)

        assert response.status_code == 400
        assert "own book" in response.json()["detail"]

    def test_create_duplicate_review(self, client):
        """Test that users cannot review the same book twice."""
        admin_headers = get_auth_headers(client, "rev_dup_admin@example.com", STRONG_PASSWORD, is_admin=True)
        user_headers = get_auth_headers(client, "rev_dup_user@example.com", STRONG_PASSWORD)

        # Create author and book
        author = create_test_author(client, "Dup Review Author", admin_headers=admin_headers)
        book = create_test_book(
            client,
            title="Duplicate Review Book",
            isbn="9781111111112",
            author_ids=[author["id"]],
            admin_headers=admin_headers
        )

        # First review
        review_data = {
            "book_id": book["id"],
            "rating": 4,
            "comment": "Good book!"
        }
        response = client.post("/api/v1/reviews", json=review_data, headers=user_headers)
        assert response.status_code == 201

        # Try second review
        review_data["rating"] = 5
        response = client.post("/api/v1/reviews", json=review_data, headers=user_headers)

        assert response.status_code == 400
        assert "already reviewed" in response.json()["detail"]

    def test_get_book_reviews_not_found(self, client):
        """Test getting reviews for non-existent book."""
        response = client.get("/api/v1/books/99999/reviews")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_book_reviews_pagination(self, client):
        """Test reviews pagination with skip and limit."""
        admin_headers = get_auth_headers(client, "rev_page_admin@example.com", STRONG_PASSWORD, is_admin=True)

        # Create author and book
        author = create_test_author(client, "Page Author", admin_headers=admin_headers)
        book = create_test_book(
            client,
            title="Paginated Book",
            isbn="9781111111113",
            author_ids=[author["id"]],
            admin_headers=admin_headers
        )

        # Create multiple reviews from different users
        for i in range(5):
            user_headers = get_auth_headers(client, f"rev_page_user{i}@example.com", STRONG_PASSWORD)
            review_data = {
                "book_id": book["id"],
                "rating": (i % 5) + 1,
                "comment": f"Review {i}"
            }
            client.post("/api/v1/reviews", json=review_data, headers=user_headers)

        # Test pagination
        response = client.get(f"/api/v1/books/{book['id']}/reviews?skip=2&limit=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_book_reviews_invalid_skip(self, client):
        """Test reviews with negative skip value."""
        admin_headers = get_auth_headers(client, "rev_neg_skip@example.com", STRONG_PASSWORD, is_admin=True)

        # Create author and book
        author = create_test_author(client, "Skip Author", admin_headers=admin_headers)
        book = create_test_book(
            client,
            title="Skip Test Book",
            isbn="9781111111114",
            author_ids=[author["id"]],
            admin_headers=admin_headers
        )

        response = client.get(f"/api/v1/books/{book['id']}/reviews?skip=-1")

        assert response.status_code == 400
        assert "non-negative" in response.json()["detail"]

    def test_get_book_reviews_invalid_limit(self, client):
        """Test reviews with zero or negative limit value."""
        admin_headers = get_auth_headers(client, "rev_neg_limit@example.com", STRONG_PASSWORD, is_admin=True)

        # Create author and book
        author = create_test_author(client, "Limit Author", admin_headers=admin_headers)
        book = create_test_book(
            client,
            title="Limit Test Book",
            isbn="9781111111115",
            author_ids=[author["id"]],
            admin_headers=admin_headers
        )

        response = client.get(f"/api/v1/books/{book['id']}/reviews?limit=0")

        assert response.status_code == 400
        assert "positive" in response.json()["detail"]

    def test_get_review_not_found(self, client):
        """Test getting a non-existent review."""
        response = client.get("/api/v1/reviews/99999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_update_review_not_found(self, client):
        """Test updating a non-existent review."""
        user_headers = get_auth_headers(client, "rev_upd_nf@example.com", STRONG_PASSWORD)

        response = client.put(
            "/api/v1/reviews/99999",
            json={"rating": 3},
            headers=user_headers
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_update_review_not_owner(self, client):
        """Test updating another user's review."""
        admin_headers = get_auth_headers(client, "rev_upd_admin@example.com", STRONG_PASSWORD, is_admin=True)
        user1_headers = get_auth_headers(client, "rev_upd_user1@example.com", STRONG_PASSWORD)
        user2_headers = get_auth_headers(client, "rev_upd_user2@example.com", STRONG_PASSWORD)

        # Create author and book
        author = create_test_author(client, "Update Author", admin_headers=admin_headers)
        book = create_test_book(
            client,
            title="Update Review Book",
            isbn="9781111111116",
            author_ids=[author["id"]],
            admin_headers=admin_headers
        )

        # User1 creates a review
        review_data = {
            "book_id": book["id"],
            "rating": 4,
            "comment": "User1's review"
        }
        response = client.post("/api/v1/reviews", json=review_data, headers=user1_headers)
        review_id = response.json()["id"]

        # User2 tries to update
        response = client.put(
            f"/api/v1/reviews/{review_id}",
            json={"rating": 1},
            headers=user2_headers
        )

        assert response.status_code == 403
        assert "own reviews" in response.json()["detail"]

    def test_update_review_partial(self, client):
        """Test partial update of a review."""
        admin_headers = get_auth_headers(client, "rev_part_admin@example.com", STRONG_PASSWORD, is_admin=True)
        user_headers = get_auth_headers(client, "rev_part_user@example.com", STRONG_PASSWORD)

        # Create author and book
        author = create_test_author(client, "Partial Author", admin_headers=admin_headers)
        book = create_test_book(
            client,
            title="Partial Update Book",
            isbn="9781111111117",
            author_ids=[author["id"]],
            admin_headers=admin_headers
        )

        # Create a review
        review_data = {
            "book_id": book["id"],
            "rating": 3,
            "comment": "Original comment"
        }
        response = client.post("/api/v1/reviews", json=review_data, headers=user_headers)
        review_id = response.json()["id"]

        # Update only rating
        response = client.put(
            f"/api/v1/reviews/{review_id}",
            json={"rating": 5},
            headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["rating"] == 5
        assert data["comment"] == "Original comment"

    def test_update_review_only_comment(self, client):
        """Test updating only the comment of a review."""
        admin_headers = get_auth_headers(client, "rev_comm_admin@example.com", STRONG_PASSWORD, is_admin=True)
        user_headers = get_auth_headers(client, "rev_comm_user@example.com", STRONG_PASSWORD)

        # Create author and book
        author = create_test_author(client, "Comment Author", admin_headers=admin_headers)
        book = create_test_book(
            client,
            title="Comment Update Book",
            isbn="9781111111118",
            author_ids=[author["id"]],
            admin_headers=admin_headers
        )

        # Create a review
        review_data = {
            "book_id": book["id"],
            "rating": 4,
            "comment": "Original comment"
        }
        response = client.post("/api/v1/reviews", json=review_data, headers=user_headers)
        review_id = response.json()["id"]

        # Update only comment
        response = client.put(
            f"/api/v1/reviews/{review_id}",
            json={"comment": "Updated comment"},
            headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["rating"] == 4
        assert data["comment"] == "Updated comment"

    def test_delete_review_not_found(self, client):
        """Test deleting a non-existent review."""
        user_headers = get_auth_headers(client, "rev_del_nf@example.com", STRONG_PASSWORD)

        response = client.delete("/api/v1/reviews/99999", headers=user_headers)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_delete_review_not_owner(self, client):
        """Test deleting another user's review (non-admin)."""
        admin_headers = get_auth_headers(client, "rev_del_admin@example.com", STRONG_PASSWORD, is_admin=True)
        user1_headers = get_auth_headers(client, "rev_del_user1@example.com", STRONG_PASSWORD)
        user2_headers = get_auth_headers(client, "rev_del_user2@example.com", STRONG_PASSWORD)

        # Create author and book
        author = create_test_author(client, "Delete Author", admin_headers=admin_headers)
        book = create_test_book(
            client,
            title="Delete Review Book",
            isbn="9781111111119",
            author_ids=[author["id"]],
            admin_headers=admin_headers
        )

        # User1 creates a review
        review_data = {
            "book_id": book["id"],
            "rating": 4,
            "comment": "User1's review"
        }
        response = client.post("/api/v1/reviews", json=review_data, headers=user1_headers)
        review_id = response.json()["id"]

        # User2 tries to delete
        response = client.delete(f"/api/v1/reviews/{review_id}", headers=user2_headers)

        assert response.status_code == 403
        assert "own reviews" in response.json()["detail"]

    def test_delete_review_admin_can_delete_any(self, client):
        """Test that admin can delete any review."""
        admin_headers = get_auth_headers(client, "rev_adm_del@example.com", STRONG_PASSWORD, is_admin=True)
        user_headers = get_auth_headers(client, "rev_user_del@example.com", STRONG_PASSWORD)

        # Create author and book
        author = create_test_author(client, "Admin Delete Author", admin_headers=admin_headers)
        book = create_test_book(
            client,
            title="Admin Delete Book",
            isbn="9781111111120",
            author_ids=[author["id"]],
            admin_headers=admin_headers
        )

        # User creates a review
        review_data = {
            "book_id": book["id"],
            "rating": 2,
            "comment": "User's review"
        }
        response = client.post("/api/v1/reviews", json=review_data, headers=user_headers)
        review_id = response.json()["id"]

        # Admin deletes user's review
        response = client.delete(f"/api/v1/reviews/{review_id}", headers=admin_headers)

        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

    def test_get_review_with_details(self, client):
        """Test getting a review with user and book details."""
        admin_headers = get_auth_headers(client, "rev_det_admin@example.com", STRONG_PASSWORD, is_admin=True)
        user_headers = get_auth_headers(client, "rev_det_user@example.com", STRONG_PASSWORD)

        # Create author and book
        author = create_test_author(client, "Details Author", admin_headers=admin_headers)
        book = create_test_book(
            client,
            title="Details Book",
            isbn="9781111111121",
            author_ids=[author["id"]],
            admin_headers=admin_headers
        )

        # Create a review
        review_data = {
            "book_id": book["id"],
            "rating": 5,
            "comment": "Excellent!"
        }
        response = client.post("/api/v1/reviews", json=review_data, headers=user_headers)
        review_id = response.json()["id"]

        # Get review with details
        response = client.get(f"/api/v1/reviews/{review_id}")

        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "book" in data
        assert data["rating"] == 5


class TestReviewsValidation:
    """Test validation rules for reviews."""

    def test_create_review_requires_auth(self, client):
        """Test that creating a review requires authentication."""
        review_data = {
            "book_id": 1,
            "rating": 5,
            "comment": "Great!"
        }

        response = client.post("/api/v1/reviews", json=review_data)

        assert response.status_code == 401

    def test_update_review_requires_auth(self, client):
        """Test that updating a review requires authentication."""
        response = client.put("/api/v1/reviews/1", json={"rating": 3})

        assert response.status_code == 401

    def test_delete_review_requires_auth(self, client):
        """Test that deleting a review requires authentication."""
        response = client.delete("/api/v1/reviews/1")

        assert response.status_code == 401

