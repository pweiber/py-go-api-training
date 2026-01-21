"""
Unit tests for Review CRUD endpoints.
"""
import pytest
from tests.conftest import get_auth_headers, STRONG_PASSWORD


def test_create_review(client):
    """Test creating a review with valid data."""
    # Create book owner
    owner_headers = get_auth_headers(client, "book_owner@example.com", STRONG_PASSWORD)

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
    reviewer_headers = get_auth_headers(client, "reviewer@example.com", STRONG_PASSWORD)

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
    owner_headers = get_auth_headers(client, "rating_owner@example.com", STRONG_PASSWORD)

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
    reviewer_headers = get_auth_headers(client, "rating_test@example.com", STRONG_PASSWORD)

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
    owner_headers = get_auth_headers(client, "one_review_owner@example.com", STRONG_PASSWORD)

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
    reviewer_headers = get_auth_headers(client, "one_reviewer@example.com", STRONG_PASSWORD)

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
    owner_headers = get_auth_headers(client, "self_review@example.com", STRONG_PASSWORD)

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
    owner_headers = get_auth_headers(client, "del_review_owner@example.com", STRONG_PASSWORD)

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
    reviewer_headers = get_auth_headers(client, "del_reviewer@example.com", STRONG_PASSWORD)

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
    owner_headers = get_auth_headers(client, "others_review_owner@example.com", STRONG_PASSWORD)

    # Create a book
    book_data = {
        "title": "Others Review Book",
        "author": "Test Author",
        "isbn": "978-7777777776",
        "published_date": "2023-01-15"
    }
    book_response = client.post("/api/v1/books", json=book_data, headers=owner_headers)
    book_id = book_response.json()["id"]

    # Create original reviewer
    reviewer1_headers = get_auth_headers(client, "orig_reviewer@example.com", STRONG_PASSWORD)

    # Create review
    review_data = {
        "book_id": book_id,
        "rating": 4,
        "comment": "Original review"
    }
    response = client.post("/api/v1/reviews", json=review_data, headers=reviewer1_headers)
    review_id = response.json()["id"]

    # Create different user who will try to delete
    reviewer2_headers = get_auth_headers(client, "other_user@example.com", STRONG_PASSWORD)

    # Try to delete another user's review
    response = client.delete(f"/api/v1/reviews/{review_id}", headers=reviewer2_headers)
    assert response.status_code == 403
    assert "only delete your own reviews" in response.json()["detail"]


def test_get_book_reviews(client):
    """Test getting all reviews for a book."""
    # Create book owner
    owner_headers = get_auth_headers(client, "book_reviews_owner@example.com", STRONG_PASSWORD)

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
        reviewer_headers = get_auth_headers(client, f"reviewer{i}@example.com", STRONG_PASSWORD)
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
    reviewer_headers = get_auth_headers(client, "bad_book_reviewer@example.com", STRONG_PASSWORD)

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
    assert response.status_code == 403  # No auth header

