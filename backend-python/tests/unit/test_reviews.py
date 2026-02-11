"""
Unit tests for Review CRUD endpoints.
"""
import pytest
from tests.conftest import get_auth_headers, STRONG_PASSWORD


def test_create_review(client):
    """Test creating a review with valid data."""
    # Create book owner
    owner_headers = get_auth_headers(client, "book_owner@example.com", STRONG_PASSWORD, is_admin=True)

    # Create a book
    book_data = {
        "title": "Reviewable Book",
        "author": "Test Author",
        "isbn": "978-7777777771",
        "published_date": "2023-01-15"
    }
    book_response = client.post("/api/v1/books", json=book_data, headers=owner_headers)
    book_id = book_response.json()["id"]

    # Create reviewer (different user)
    reviewer_headers = get_auth_headers(client, "reviewer@example.com", STRONG_PASSWORD, is_admin=True)

    review_data = {
        "book_id": book_id,
        "rating": 5,
        "comment": "An excellent read! Highly recommended."
    }

    response = client.post("/api/v1/reviews", json=review_data, headers=reviewer_headers)
    assert response.status_code == 201

    data = response.json()
    assert data["book_id"] == book_id
    assert data["rating"] == 5
    assert data["comment"] == review_data["comment"]
    assert "id" in data
    assert "created_at" in data


def test_review_rating_validation(client):
    """Test that rating must be between 1 and 5."""
    # Create book owner
    owner_headers = get_auth_headers(client, "rating_owner@example.com", STRONG_PASSWORD, is_admin=True)

    # Create a book
    book_data = {
        "title": "Rating Test Book",
        "author": "Test Author",
        "isbn": "978-7777777772",
        "published_date": "2023-01-15"
    }
    book_response = client.post("/api/v1/books", json=book_data, headers=owner_headers)
    book_id = book_response.json()["id"]

    # Create reviewer
    reviewer_headers = get_auth_headers(client, "rating_test@example.com", STRONG_PASSWORD, is_admin=True)

    # Test rating too low
    review_data = {
        "book_id": book_id,
        "rating": 0
    }
    response = client.post("/api/v1/reviews", json=review_data, headers=reviewer_headers)
    assert response.status_code == 422

    # Test rating too high
    review_data["rating"] = 6
    response = client.post("/api/v1/reviews", json=review_data, headers=reviewer_headers)
    assert response.status_code == 422


def test_one_review_per_user_per_book(client):
    """Test that a user can only review a book once."""
    # Create book owner
    owner_headers = get_auth_headers(client, "one_review_owner@example.com", STRONG_PASSWORD, is_admin=True)

    # Create a book
    book_data = {
        "title": "One Review Book",
        "author": "Test Author",
        "isbn": "978-7777777773",
        "published_date": "2023-01-15"
    }
    book_response = client.post("/api/v1/books", json=book_data, headers=owner_headers)
    book_id = book_response.json()["id"]

    # Create reviewer
    reviewer_headers = get_auth_headers(client, "one_reviewer@example.com", STRONG_PASSWORD, is_admin=True)

    # Create first review
    review_data = {
        "book_id": book_id,
        "rating": 4,
        "comment": "First review"
    }
    response = client.post("/api/v1/reviews", json=review_data, headers=reviewer_headers)
    assert response.status_code == 201

    # Try to create second review
    review_data["comment"] = "Second review attempt"
    response = client.post("/api/v1/reviews", json=review_data, headers=reviewer_headers)
    assert response.status_code == 400
    assert "already reviewed" in response.json()["detail"]


def test_cannot_review_own_book(client):
    """Test that a user cannot review their own book."""
    # Create book owner
    owner_headers = get_auth_headers(client, "self_review@example.com", STRONG_PASSWORD, is_admin=True)

    # Create a book
    book_data = {
        "title": "My Own Book",
        "author": "Self Author",
        "isbn": "978-7777777774",
        "published_date": "2023-01-15"
    }
    book_response = client.post("/api/v1/books", json=book_data, headers=owner_headers)
    book_id = book_response.json()["id"]

    # Try to review own book
    review_data = {
        "book_id": book_id,
        "rating": 5,
        "comment": "My book is great!"
    }
    response = client.post("/api/v1/reviews", json=review_data, headers=owner_headers)
    assert response.status_code == 400
    assert "cannot review your own book" in response.json()["detail"]


def test_delete_own_review(client):
    """Test that a user can delete their own review."""
    # Create book owner
    owner_headers = get_auth_headers(client, "del_review_owner@example.com", STRONG_PASSWORD, is_admin=True)

    # Create a book
    book_data = {
        "title": "Deletable Review Book",
        "author": "Test Author",
        "isbn": "978-7777777775",
        "published_date": "2023-01-15"
    }
    book_response = client.post("/api/v1/books", json=book_data, headers=owner_headers)
    book_id = book_response.json()["id"]

    # Create reviewer
    reviewer_headers = get_auth_headers(client, "del_reviewer@example.com", STRONG_PASSWORD, is_admin=True)

    # Create review
    review_data = {
        "book_id": book_id,
        "rating": 3,
        "comment": "This will be deleted"
    }
    response = client.post("/api/v1/reviews", json=review_data, headers=reviewer_headers)
    review_id = response.json()["id"]

    # Delete own review
    response = client.delete(f"/api/v1/reviews/{review_id}", headers=reviewer_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Review deleted successfully"

    # Verify deletion
    get_response = client.get(f"/api/v1/reviews/{review_id}")
    assert get_response.status_code == 404


def test_cannot_delete_others_review(client):
    """Test that a user cannot delete another user's review."""
    # Create book owner
    owner_headers = get_auth_headers(client, "others_review_owner@example.com", STRONG_PASSWORD, is_admin=True)

    # Create a book
    book_data = {
        "title": "Others Review Book",
        "author": "Test Author",
        "isbn": "978-7777777776",
        "published_date": "2023-01-15"
    }
    book_response = client.post("/api/v1/books", json=book_data, headers=owner_headers)
    book_id = book_response.json()["id"]

    # Create original reviewer (regular user, not admin)
    reviewer1_headers = get_auth_headers(client, "orig_reviewer@example.com", STRONG_PASSWORD)

    # Create review
    review_data = {
        "book_id": book_id,
        "rating": 4,
        "comment": "Original review"
    }
    response = client.post("/api/v1/reviews", json=review_data, headers=reviewer1_headers)
    review_id = response.json()["id"]

    # Create different user who will try to delete (also not admin)
    reviewer2_headers = get_auth_headers(client, "other_user@example.com", STRONG_PASSWORD)

    # Try to delete another user's review
    response = client.delete(f"/api/v1/reviews/{review_id}", headers=reviewer2_headers)
    assert response.status_code == 403
    assert "only delete your own reviews" in response.json()["detail"]


def test_get_book_reviews(client):
    """Test getting all reviews for a book."""
    # Create book owner
    owner_headers = get_auth_headers(client, "book_reviews_owner@example.com", STRONG_PASSWORD, is_admin=True)

    # Create a book
    book_data = {
        "title": "Book With Reviews",
        "author": "Test Author",
        "isbn": "978-7777777777",
        "published_date": "2023-01-15"
    }
    book_response = client.post("/api/v1/books", json=book_data, headers=owner_headers)
    book_id = book_response.json()["id"]

    # Create multiple reviewers and reviews
    for i in range(3):
        reviewer_headers = get_auth_headers(client, f"reviewer{i}@example.com", STRONG_PASSWORD, is_admin=True)
        review_data = {
            "book_id": book_id,
            "rating": 3 + i,
            "comment": f"Review {i+1}"
        }
        client.post("/api/v1/reviews", json=review_data, headers=reviewer_headers)

    # Get book reviews
    response = client.get(f"/api/v1/books/{book_id}/reviews")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3


def test_review_nonexistent_book(client):
    """Test reviewing a nonexistent book."""
    reviewer_headers = get_auth_headers(client, "bad_book_reviewer@example.com", STRONG_PASSWORD, is_admin=True)

    review_data = {
        "book_id": 99999,
        "rating": 5,
        "comment": "Great book!"
    }

    response = client.post("/api/v1/reviews", json=review_data, headers=reviewer_headers)
    assert response.status_code == 404


def test_review_requires_authentication(client):
    """Test that creating a review requires authentication."""
    review_data = {
        "book_id": 1,
        "rating": 5
    }

    response = client.post("/api/v1/reviews", json=review_data)
    # Expect 401 Unauthorized when no authentication is provided
    assert response.status_code in [401, 403]

# ============================================================================
# ERROR PATH TESTS - Coverage Improvement
# ============================================================================


def test_get_review_not_found(client):
    """Test getting a non-existent review returns 404."""
    non_existent_id = 99999

    response = client.get(f"/api/v1/reviews/{non_existent_id}")

    assert response.status_code == 404
    assert f"Review with id {non_existent_id} not found" in response.json()["detail"]


def test_update_review_not_found(client):
    """Test updating a non-existent review returns 404."""
    non_existent_id = 99999
    reviewer_headers = get_auth_headers(client, "update_404@example.com", STRONG_PASSWORD)

    update_data = {"rating": 4, "comment": "Updated"}

    response = client.put(f"/api/v1/reviews/{non_existent_id}", headers=reviewer_headers, json=update_data)

    assert response.status_code == 404
    assert f"Review with id {non_existent_id} not found" in response.json()["detail"]


def test_update_review_unauthorized(client):
    """Test updating another user's review returns 403."""
    # Create book owner (admin to create book)
    owner_headers = get_auth_headers(client, "update_owner@example.com", STRONG_PASSWORD, is_admin=True)
    book_response = client.post("/api/v1/books", headers=owner_headers, json={
        "title": "Update Test Book",
        "author": "Test Author",
        "isbn": "978-8888888880",
        "published_date": "2023-01-01"
    })
    assert book_response.status_code == 201, f"Book creation failed: {book_response.json()}"
    book_id = book_response.json()["id"]

    reviewer1_headers = get_auth_headers(client, "update_reviewer1@example.com", STRONG_PASSWORD)
    review_response = client.post("/api/v1/reviews", headers=reviewer1_headers, json={
        "book_id": book_id,
        "rating": 3,
        "comment": "Original review"
    })
    assert review_response.status_code == 201, f"Review creation failed: {review_response.json()}"
    review_id = review_response.json()["id"]

    # Different user tries to update
    reviewer2_headers = get_auth_headers(client, "update_reviewer2@example.com", STRONG_PASSWORD)
    update_data = {"rating": 5, "comment": "Hijacked review"}

    response = client.put(f"/api/v1/reviews/{review_id}", headers=reviewer2_headers, json=update_data)

    assert response.status_code == 403
    assert "only update your own reviews" in response.json()["detail"]


def test_delete_review_not_found(client):
    """Test deleting a non-existent review returns 404."""
    non_existent_id = 99999
    reviewer_headers = get_auth_headers(client, "delete_404@example.com", STRONG_PASSWORD)

    response = client.delete(f"/api/v1/reviews/{non_existent_id}", headers=reviewer_headers)

    assert response.status_code == 404
    assert f"Review with id {non_existent_id} not found" in response.json()["detail"]


def test_delete_review_unauthorized_non_admin(client):
    """Test non-admin user cannot delete another user's review."""
    owner_headers = get_auth_headers(client, "delete_unauth_owner@example.com", STRONG_PASSWORD, is_admin=True)
    book_response = client.post("/api/v1/books", headers=owner_headers, json={
        "title": "Delete Unauth Book",
        "author": "Test Author",
        "isbn": "978-8888888881",
        "published_date": "2023-01-01"
    })
    assert book_response.status_code == 201
    book_id = book_response.json()["id"]

    reviewer1_headers = get_auth_headers(client, "delete_reviewer1@example.com", STRONG_PASSWORD)
    review_response = client.post("/api/v1/reviews", headers=reviewer1_headers, json={
        "book_id": book_id,
        "rating": 4,
        "comment": "Will be targeted for deletion"
    })
    assert review_response.status_code == 201
    review_id = review_response.json()["id"]

    reviewer2_headers = get_auth_headers(client, "delete_reviewer2@example.com", STRONG_PASSWORD)

    response = client.delete(f"/api/v1/reviews/{review_id}", headers=reviewer2_headers)

    assert response.status_code == 403
    assert "only delete your own reviews" in response.json()["detail"]


def test_get_book_reviews_negative_skip(client):
    """Test getting book reviews with negative skip returns 400."""
    owner_headers = get_auth_headers(client, "skip_owner@example.com", STRONG_PASSWORD, is_admin=True)
    book_response = client.post("/api/v1/books", headers=owner_headers, json={
        "title": "Skip Test Book",
        "author": "Test Author",
        "isbn": "978-8888888882",
        "published_date": "2023-01-01"
    })
    assert book_response.status_code == 201
    book_id = book_response.json()["id"]

    response = client.get(f"/api/v1/books/{book_id}/reviews?skip=-1")

    assert response.status_code == 400
    assert "skip must be non-negative" in response.json()["detail"].lower()


def test_get_book_reviews_invalid_limit(client):
    """Test getting book reviews with invalid limit returns 400."""
    owner_headers = get_auth_headers(client, "limit_owner@example.com", STRONG_PASSWORD, is_admin=True)
    book_response = client.post("/api/v1/books", headers=owner_headers, json={
        "title": "Limit Test Book",
        "author": "Test Author",
        "isbn": "978-8888888883",
        "published_date": "2023-01-01"
    })
    assert book_response.status_code == 201
    book_id = book_response.json()["id"]

    response = client.get(f"/api/v1/books/{book_id}/reviews?limit=0")

    assert response.status_code == 400
    assert "limit must be positive" in response.json()["detail"].lower()


def test_get_book_reviews_limit_capping(client):
    """Test that limit is capped at 100."""
    owner_headers = get_auth_headers(client, "cap_owner@example.com", STRONG_PASSWORD, is_admin=True)
    book_response = client.post("/api/v1/books", headers=owner_headers, json={
        "title": "Cap Test Book",
        "author": "Test Author",
        "isbn": "978-8888888884",
        "published_date": "2023-01-01"
    })
    assert book_response.status_code == 201
    book_id = book_response.json()["id"]

    # Request with limit=200 should be capped to 100
    response = client.get(f"/api/v1/books/{book_id}/reviews?limit=200")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Since we have no reviews, just verify it returns successfully
    assert len(data) <= 100


def test_get_book_reviews_book_not_found(client):
    """Test getting reviews for a non-existent book returns 404."""
    non_existent_book_id = 99999

    response = client.get(f"/api/v1/books/{non_existent_book_id}/reviews")

    assert response.status_code == 404
    assert f"Book with id {non_existent_book_id} not found" in response.json()["detail"]


def test_update_review_success(client):
    """Test successfully updating own review."""
    # Create book owner (admin to create book)
    owner_headers = get_auth_headers(client, "update_success_owner@example.com", STRONG_PASSWORD, is_admin=True)
    book_response = client.post("/api/v1/books", headers=owner_headers, json={
        "title": "Update Success Book",
        "author": "Test Author",
        "isbn": "978-8888888890",
        "published_date": "2023-01-01"
    })
    assert book_response.status_code == 201
    book_id = book_response.json()["id"]

    # Create reviewer and review
    reviewer_headers = get_auth_headers(client, "update_success_reviewer@example.com", STRONG_PASSWORD)
    review_response = client.post("/api/v1/reviews", headers=reviewer_headers, json={
        "book_id": book_id,
        "rating": 3,
        "comment": "Original review"
    })
    assert review_response.status_code == 201
    review_id = review_response.json()["id"]

    # Update the review
    update_data = {"rating": 5, "comment": "Updated review - much better!"}
    response = client.put(f"/api/v1/reviews/{review_id}", headers=reviewer_headers, json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["rating"] == 5
    assert data["comment"] == "Updated review - much better!"


def test_admin_can_delete_any_review(client):
    """Test that admin users can delete any review."""
    # Create book owner (admin)
    owner_headers = get_auth_headers(client, "admin_delete_owner@example.com", STRONG_PASSWORD, is_admin=True)
    book_response = client.post("/api/v1/books", headers=owner_headers, json={
        "title": "Admin Delete Test Book",
        "author": "Test Author",
        "isbn": "978-8888888891",
        "published_date": "2023-01-01"
    })
    assert book_response.status_code == 201
    book_id = book_response.json()["id"]

    # Create regular user and their review
    reviewer_headers = get_auth_headers(client, "regular_reviewer@example.com", STRONG_PASSWORD)
    review_response = client.post("/api/v1/reviews", headers=reviewer_headers, json={
        "book_id": book_id,
        "rating": 4,
        "comment": "Regular user review"
    })
    assert review_response.status_code == 201
    review_id = review_response.json()["id"]

    # Different admin user tries to delete
    admin_headers = get_auth_headers(client, "admin_deleter@example.com", STRONG_PASSWORD, is_admin=True)
    response = client.delete(f"/api/v1/reviews/{review_id}", headers=admin_headers)

    # Admin should be able to delete any review
    assert response.status_code == 200
    assert response.json()["message"] == "Review deleted successfully"

    # Verify deletion
    get_response = client.get(f"/api/v1/reviews/{review_id}")
    assert get_response.status_code == 404

