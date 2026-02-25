"""
Unit tests for Statistics endpoint.
"""
import pytest
from tests.conftest import get_auth_headers, create_test_author, create_test_book, create_test_category, STRONG_PASSWORD


def test_statistics_returns_counts(client):
    """Test that statistics endpoint returns all required fields."""
    response = client.get("/api/v1/stats")
    assert response.status_code == 200

    data = response.json()
    assert "total_books" in data
    assert "total_authors" in data
    assert "total_categories" in data
    assert "total_reviews" in data
    assert "average_rating" in data

    # All counts should be integers
    assert isinstance(data["total_books"], int)
    assert isinstance(data["total_authors"], int)
    assert isinstance(data["total_categories"], int)
    assert isinstance(data["total_reviews"], int)


def test_statistics_empty_database(client):
    """Test statistics with empty database."""
    response = client.get("/api/v1/stats")
    assert response.status_code == 200

    data = response.json()
    assert data["total_books"] == 0
    assert data["total_authors"] == 0
    assert data["total_categories"] == 0
    assert data["total_reviews"] == 0
    assert data["average_rating"] is None  # No reviews = no average


def test_statistics_with_data(client):
    """Test statistics with actual data."""
    admin_headers = get_auth_headers(client, "stats_user@example.com", STRONG_PASSWORD, is_admin=True)

    # Create authors
    for i in range(3):
        create_test_author(client, f"Author {i}", admin_headers=admin_headers)

    # Create categories
    for i in range(2):
        create_test_category(client, f"Category {i}", admin_headers=admin_headers)

    # Create books (requires admin)
    for i in range(5):
        create_test_book(
            client,
            title=f"Stats Book {i}",
            isbn=f"978555555555{i}",
            published_date="2023-01-15",
            admin_headers=admin_headers
        )

    response = client.get("/api/v1/stats")
    assert response.status_code == 200

    data = response.json()
    assert data["total_books"] >= 5
    assert data["total_authors"] >= 3
    assert data["total_categories"] >= 2


def test_statistics_average_rating(client):
    """Test that average rating is calculated correctly."""
    # Create admin and books
    admin_headers = get_auth_headers(client, "stats_avg_owner@example.com", STRONG_PASSWORD, is_admin=True)

    # Create books
    book_ids = []
    for i in range(2):
        book = create_test_book(
            client,
            title=f"Avg Rating Book {i}",
            isbn=f"978666666666{i}",
            published_date="2023-01-15",
            admin_headers=admin_headers
        )
        book_ids.append(book["id"])

    # Create reviews with known ratings
    ratings = [5, 4, 3, 4, 5]  # Average should be 4.2
    for i, rating in enumerate(ratings):
        reviewer_headers = get_auth_headers(client, f"stats_reviewer{i}@example.com", STRONG_PASSWORD)
        book_id = book_ids[i % len(book_ids)]  # Alternate between books
        client.post("/api/v1/reviews", json={"book_id": book_id, "rating": rating}, headers=reviewer_headers)

    response = client.get("/api/v1/stats")
    assert response.status_code == 200

    data = response.json()
    assert data["total_reviews"] >= 5
    assert data["average_rating"] is not None
    # The average of [5, 4, 3, 4, 5] = 21/5 = 4.2
    assert data["average_rating"] == pytest.approx(4.2, abs=0.1)


def test_statistics_no_authentication_required(client):
    """Test that statistics endpoint doesn't require authentication."""
    response = client.get("/api/v1/stats")
    assert response.status_code == 200

