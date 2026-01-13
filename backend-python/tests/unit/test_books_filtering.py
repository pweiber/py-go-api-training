"""
Unit tests for Book filtering and pagination.
"""
import pytest
from tests.conftest import get_auth_headers, STRONG_PASSWORD


def test_pagination_response_structure(client):
    """Test that paginated response has correct structure."""
    auth_headers = get_auth_headers(client, "paginator@example.com", STRONG_PASSWORD)

    # Create a book
    book_data = {
        "title": "Pagination Test Book",
        "author": "Test Author",
        "isbn": "978-8888888881",
        "published_date": "2023-01-15"
    }
    client.post("/api/v1/books", json=book_data, headers=auth_headers)

    response = client.get("/api/v1/books")
    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data
    assert "pages" in data

    assert isinstance(data["items"], list)
    assert isinstance(data["total"], int)
    assert isinstance(data["page"], int)
    assert isinstance(data["size"], int)
    assert isinstance(data["pages"], int)


def test_pagination_defaults(client):
    """Test default pagination values."""
    response = client.get("/api/v1/books")
    assert response.status_code == 200

    data = response.json()
    assert data["page"] == 1
    assert data["size"] == 10


def test_pagination_custom_page_size(client):
    """Test custom page and size parameters."""
    auth_headers = get_auth_headers(client, "custom_page@example.com", STRONG_PASSWORD)

    # Create multiple books
    for i in range(15):
        book_data = {
            "title": f"Book {i+1}",
            "author": "Test Author",
            "isbn": f"978-999999{i:04d}",
            "published_date": "2023-01-15"
        }
        client.post("/api/v1/books", json=book_data, headers=auth_headers)

    # Test page 1, size 5
    response = client.get("/api/v1/books?page=1&size=5")
    assert response.status_code == 200

    data = response.json()
    assert data["page"] == 1
    assert data["size"] == 5
    assert len(data["items"]) == 5
    assert data["total"] >= 15
    assert data["pages"] >= 3


def test_search_by_title(client):
    """Test searching books by title."""
    auth_headers = get_auth_headers(client, "searcher@example.com", STRONG_PASSWORD)

    # Create books with different titles
    books = [
        {"title": "Python Programming", "isbn": "978-1111111101"},
        {"title": "Java Fundamentals", "isbn": "978-1111111102"},
        {"title": "Advanced Python", "isbn": "978-1111111103"},
    ]

    for book in books:
        book_data = {
            **book,
            "author": "Test Author",
            "published_date": "2023-01-15"
        }
        client.post("/api/v1/books", json=book_data, headers=auth_headers)

    # Search for "Python"
    response = client.get("/api/v1/books?search=Python")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] >= 2
    for item in data["items"]:
        assert "python" in item["title"].lower() or "python" in (item["description"] or "").lower()


def test_search_by_description(client):
    """Test searching books by description."""
    auth_headers = get_auth_headers(client, "desc_search@example.com", STRONG_PASSWORD)

    # Create a book with specific description
    book_data = {
        "title": "Generic Title",
        "author": "Test Author",
        "isbn": "978-1111111104",
        "published_date": "2023-01-15",
        "description": "This book covers machine learning fundamentals"
    }
    client.post("/api/v1/books", json=book_data, headers=auth_headers)

    # Search for "machine learning"
    response = client.get("/api/v1/books?search=machine%20learning")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] >= 1


def test_filter_by_author_id(client):
    """Test filtering books by author ID."""
    auth_headers = get_auth_headers(client, "author_filter@example.com", STRONG_PASSWORD)

    # Create an author
    author_response = client.post("/api/v1/authors", json={"name": "Filter Author"}, headers=auth_headers)
    author_id = author_response.json()["id"]

    # Create books with and without author_id
    book_with_author = {
        "title": "Book With Author",
        "author": "Filter Author",
        "author_id": author_id,
        "isbn": "978-1111111105",
        "published_date": "2023-01-15"
    }
    book_without_author = {
        "title": "Book Without Author",
        "author": "Unknown",
        "isbn": "978-1111111106",
        "published_date": "2023-01-15"
    }

    client.post("/api/v1/books", json=book_with_author, headers=auth_headers)
    client.post("/api/v1/books", json=book_without_author, headers=auth_headers)

    # Filter by author_id
    response = client.get(f"/api/v1/books?author_id={author_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert item["author_id"] == author_id


def test_filter_by_category(client):
    """Test filtering books by category name."""
    auth_headers = get_auth_headers(client, "cat_filter@example.com", STRONG_PASSWORD, role="admin")

    # Create a category
    cat_response = client.post("/api/v1/categories", json={"name": "Science Fiction"}, headers=auth_headers)
    cat_id = cat_response.json()["id"]

    # Create a book and assign category
    book_data = {
        "title": "Sci-Fi Book",
        "author": "Test Author",
        "isbn": "978-1111111107",
        "published_date": "2023-01-15"
    }
    book_response = client.post("/api/v1/books", json=book_data, headers=auth_headers)
    book_id = book_response.json()["id"]

    client.put(
        f"/api/v1/books/{book_id}/categories",
        json={"category_ids": [cat_id]},
        headers=auth_headers
    )

    # Filter by category name
    response = client.get("/api/v1/books?category=Science%20Fiction")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] >= 1


def test_filter_by_min_rating(client):
    """Test filtering books by minimum average rating."""
    # Create book owner
    owner_headers = get_auth_headers(client, "rating_filter_owner@example.com", STRONG_PASSWORD)

    # Create two books
    book1_data = {
        "title": "High Rated Book",
        "author": "Test Author",
        "isbn": "978-1111111108",
        "published_date": "2023-01-15"
    }
    book2_data = {
        "title": "Low Rated Book",
        "author": "Test Author",
        "isbn": "978-1111111109",
        "published_date": "2023-01-15"
    }

    book1_response = client.post("/api/v1/books", json=book1_data, headers=owner_headers)
    book2_response = client.post("/api/v1/books", json=book2_data, headers=owner_headers)

    book1_id = book1_response.json()["id"]
    book2_id = book2_response.json()["id"]

    # Create reviewers and add reviews
    reviewer1_headers = get_auth_headers(client, "high_rater@example.com", STRONG_PASSWORD)
    reviewer2_headers = get_auth_headers(client, "low_rater@example.com", STRONG_PASSWORD)

    # High rating for book1
    client.post("/api/v1/reviews", json={"book_id": book1_id, "rating": 5}, headers=reviewer1_headers)
    client.post("/api/v1/reviews", json={"book_id": book1_id, "rating": 5}, headers=reviewer2_headers)

    # Low rating for book2
    client.post("/api/v1/reviews", json={"book_id": book2_id, "rating": 2}, headers=reviewer1_headers)
    client.post("/api/v1/reviews", json={"book_id": book2_id, "rating": 2}, headers=reviewer2_headers)

    # Filter by min_rating=4
    response = client.get("/api/v1/books?min_rating=4")
    assert response.status_code == 200

    data = response.json()
    # Should find the high-rated book
    for item in data["items"]:
        if item["average_rating"] is not None:
            assert item["average_rating"] >= 4


def test_combined_filters(client):
    """Test using multiple filters together."""
    auth_headers = get_auth_headers(client, "combined_filter@example.com", STRONG_PASSWORD, role="admin")

    # Create an author
    author_response = client.post("/api/v1/authors", json={"name": "Combined Author"}, headers=auth_headers)
    author_id = author_response.json()["id"]

    # Create a category
    cat_response = client.post("/api/v1/categories", json={"name": "Combined Category"}, headers=auth_headers)
    cat_id = cat_response.json()["id"]

    # Create a book with author, category, and searchable title
    book_data = {
        "title": "Combined Filter Test",
        "author": "Combined Author",
        "author_id": author_id,
        "isbn": "978-1111111110",
        "published_date": "2023-01-15"
    }
    book_response = client.post("/api/v1/books", json=book_data, headers=auth_headers)
    book_id = book_response.json()["id"]

    # Assign category
    client.put(
        f"/api/v1/books/{book_id}/categories",
        json={"category_ids": [cat_id]},
        headers=auth_headers
    )

    # Search with multiple filters
    response = client.get(
        f"/api/v1/books?search=Combined&author_id={author_id}&category=Combined%20Category&page=1&size=5"
    )
    assert response.status_code == 200

    data = response.json()
    assert data["total"] >= 1
    assert data["page"] == 1
    assert data["size"] == 5


def test_empty_search_results(client):
    """Test search with no matching results."""
    response = client.get("/api/v1/books?search=nonexistentbooktitle12345")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 0
    assert len(data["items"]) == 0
    assert data["pages"] == 1


def test_book_response_includes_categories(client):
    """Test that book response includes categories."""
    auth_headers = get_auth_headers(client, "cat_response@example.com", STRONG_PASSWORD, role="admin")

    # Create a category
    cat_response = client.post("/api/v1/categories", json={"name": "Response Test"}, headers=auth_headers)
    cat_id = cat_response.json()["id"]

    # Create a book
    book_data = {
        "title": "Category Response Book",
        "author": "Test Author",
        "isbn": "978-1111111111",
        "published_date": "2023-01-15"
    }
    book_response = client.post("/api/v1/books", json=book_data, headers=auth_headers)
    book_id = book_response.json()["id"]

    # Assign category
    client.put(
        f"/api/v1/books/{book_id}/categories",
        json={"category_ids": [cat_id]},
        headers=auth_headers
    )

    # Get single book
    response = client.get(f"/api/v1/books/{book_id}")
    assert response.status_code == 200

    data = response.json()
    assert "categories" in data
    assert len(data["categories"]) == 1
    assert data["categories"][0]["name"] == "Response Test"


def test_book_response_includes_average_rating(client):
    """Test that book response includes average rating."""
    # Create book owner
    owner_headers = get_auth_headers(client, "avg_rating_owner@example.com", STRONG_PASSWORD)

    # Create a book
    book_data = {
        "title": "Rated Book",
        "author": "Test Author",
        "isbn": "978-1111111112",
        "published_date": "2023-01-15"
    }
    book_response = client.post("/api/v1/books", json=book_data, headers=owner_headers)
    book_id = book_response.json()["id"]

    # Create reviewers and add reviews
    for i, rating in enumerate([4, 5, 3]):
        reviewer_headers = get_auth_headers(client, f"avg_rater{i}@example.com", STRONG_PASSWORD)
        client.post("/api/v1/reviews", json={"book_id": book_id, "rating": rating}, headers=reviewer_headers)

    # Get book
    response = client.get(f"/api/v1/books/{book_id}")
    assert response.status_code == 200

    data = response.json()
    assert "average_rating" in data
    assert data["average_rating"] == 4.0  # (4+5+3)/3 = 4

