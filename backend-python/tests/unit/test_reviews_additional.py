"""
Additional tests for reviews to increase coverage.
"""
import pytest
from tests.conftest import get_auth_headers, create_test_author, create_test_book, STRONG_PASSWORD


def test_create_review_for_nonexistent_book(client):
    """Test creating a review for a book that doesn't exist."""
    user_headers = get_auth_headers(client, "reviewer_nobook@test.com", STRONG_PASSWORD)

    review_data = {
        "book_id": 99999,
        "rating": 5,
        "comment": "Great book!"
    }

    response = client.post("/api/v1/reviews", json=review_data, headers=user_headers)
    assert response.status_code == 404


def test_update_review_not_found(client):
    """Test updating a review that doesn't exist."""
    user_headers = get_auth_headers(client, "reviewer_noupd@test.com", STRONG_PASSWORD)

    update_data = {
        "rating": 4,
        "comment": "Updated review"
    }

    response = client.put("/api/v1/reviews/99999", json=update_data, headers=user_headers)
    assert response.status_code == 404


def test_delete_review_not_found(client):
    """Test deleting a review that doesn't exist."""
    user_headers = get_auth_headers(client, "reviewer_nodel@test.com", STRONG_PASSWORD)

    response = client.delete("/api/v1/reviews/99999", headers=user_headers)
    assert response.status_code == 404


def test_get_review_not_found(client):
    """Test getting a review that doesn't exist."""
    response = client.get("/api/v1/reviews/99999")
    assert response.status_code == 404


def test_update_review_by_non_owner(client):
    """Test that users can only update their own reviews."""
    admin_headers = get_auth_headers(client, "admin_rev@test.com", STRONG_PASSWORD, is_admin=True)
    user1_headers = get_auth_headers(client, "user1_rev@test.com", STRONG_PASSWORD)
    user2_headers = get_auth_headers(client, "user2_rev@test.com", STRONG_PASSWORD)

    # Create a book
    author = create_test_author(client, "Test Author", admin_headers=admin_headers)
    book = create_test_book(client, "Test Book", isbn="9781111111111", author_ids=[author["id"]], admin_headers=admin_headers)

    # User 1 creates a review
    review_data = {
        "book_id": book["id"],
        "rating": 5,
        "comment": "Great!"
    }
    create_response = client.post("/api/v1/reviews", json=review_data, headers=user1_headers)
    review_id = create_response.json()["id"]

    # User 2 tries to update it
    update_data = {
        "rating": 1,
        "comment": "Actually terrible"
    }
    response = client.put(f"/api/v1/reviews/{review_id}", json=update_data, headers=user2_headers)
    assert response.status_code == 403


def test_delete_review_by_non_owner(client):
    """Test that users can only delete their own reviews."""
    admin_headers = get_auth_headers(client, "admin_rev2@test.com", STRONG_PASSWORD, is_admin=True)
    user1_headers = get_auth_headers(client, "user1_rev2@test.com", STRONG_PASSWORD)
    user2_headers = get_auth_headers(client, "user2_rev2@test.com", STRONG_PASSWORD)

    # Create a book
    author = create_test_author(client, "Test Author 2", admin_headers=admin_headers)
    book = create_test_book(client, "Test Book 2", isbn="9782222222222", author_ids=[author["id"]], admin_headers=admin_headers)

    # User 1 creates a review
    review_data = {
        "book_id": book["id"],
        "rating": 5,
        "comment": "Great!"
    }
    create_response = client.post("/api/v1/reviews", json=review_data, headers=user1_headers)
    review_id = create_response.json()["id"]

    # User 2 tries to delete it
    response = client.delete(f"/api/v1/reviews/{review_id}", headers=user2_headers)
    assert response.status_code == 403


def test_list_reviews_for_book(client):
    """Test listing all reviews for a specific book."""
    admin_headers = get_auth_headers(client, "admin_revlist@test.com", STRONG_PASSWORD, is_admin=True)
    user_headers = get_auth_headers(client, "user_revlist@test.com", STRONG_PASSWORD)

    # Create a book
    author = create_test_author(client, "Author Rev", admin_headers=admin_headers)
    book = create_test_book(client, "Book with Reviews", isbn="9783333333333", author_ids=[author["id"]], admin_headers=admin_headers)

    # Create a review
    review_data = {
        "book_id": book["id"],
        "rating": 4,
        "comment": "Good book"
    }
    client.post("/api/v1/reviews", json=review_data, headers=user_headers)

    # List reviews for this book using correct endpoint
    response = client.get(f"/api/v1/books/{book['id']}/reviews")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_create_review_without_comment(client):
    """Test creating a review without a comment (optional field)."""
    admin_headers = get_auth_headers(client, "admin_nocom@test.com", STRONG_PASSWORD, is_admin=True)
    user_headers = get_auth_headers(client, "user_nocom@test.com", STRONG_PASSWORD)

    # Create a book
    author = create_test_author(client, "Author NoComment", admin_headers=admin_headers)
    book = create_test_book(client, "Book NoComment", isbn="9784444444444", author_ids=[author["id"]], admin_headers=admin_headers)

    # Create review without comment
    review_data = {
        "book_id": book["id"],
        "rating": 3
    }

    response = client.post("/api/v1/reviews", json=review_data, headers=user_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["rating"] == 3
    assert data["comment"] is None or data["comment"] == ""


def test_update_review_partial(client):
    """Test partially updating a review (only rating or only comment)."""
    admin_headers = get_auth_headers(client, "admin_partial@test.com", STRONG_PASSWORD, is_admin=True)
    user_headers = get_auth_headers(client, "user_partial@test.com", STRONG_PASSWORD)

    # Create a book
    author = create_test_author(client, "Author Partial", admin_headers=admin_headers)
    book = create_test_book(client, "Book Partial", isbn="9785555555555", author_ids=[author["id"]], admin_headers=admin_headers)

    # Create a review
    review_data = {
        "book_id": book["id"],
        "rating": 3,
        "comment": "OK book"
    }
    create_response = client.post("/api/v1/reviews", json=review_data, headers=user_headers)
    review_id = create_response.json()["id"]

    # Update only the rating
    update_data = {
        "rating": 5
    }
    response = client.put(f"/api/v1/reviews/{review_id}", json=update_data, headers=user_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["rating"] == 5
    assert data["comment"] == "OK book"  # Should remain unchanged

