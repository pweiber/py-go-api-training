"""
Unit tests for Book filtering and pagination.
"""
import pytest
from tests.conftest import get_auth_headers, create_test_author, create_test_book, create_test_category, STRONG_PASSWORD


def test_pagination_response_structure(client):
    """Test that paginated response has correct structure."""
    admin_headers = get_auth_headers(client, "paginator@example.com", STRONG_PASSWORD, is_admin=True)

    # Create a book using helper
    create_test_book(client, title="Pagination Test Book", isbn="9788888888881", admin_headers=admin_headers)

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
    admin_headers = get_auth_headers(client, "custom_page@example.com", STRONG_PASSWORD, is_admin=True)

    # Create multiple books
    for i in range(15):
        create_test_book(
            client,
            title=f"Book {i+1}",
            isbn=f"978999999{i:04d}",
            published_date="2023-01-15",
            admin_headers=admin_headers
        )

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
    admin_headers = get_auth_headers(client, "searcher@example.com", STRONG_PASSWORD, is_admin=True)

    # Create books with different titles
    create_test_book(client, title="Python Programming", isbn="9781111111101", admin_headers=admin_headers)
    create_test_book(client, title="Java Fundamentals", isbn="9781111111102", admin_headers=admin_headers)
    create_test_book(client, title="Advanced Python", isbn="9781111111103", admin_headers=admin_headers)

    # Search for "Python"
    response = client.get("/api/v1/books?search=Python")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] >= 2
    for item in data["items"]:
        assert "python" in item["title"].lower() or "python" in (item["description"] or "").lower()


def test_search_by_description(client):
    """Test searching books by description."""
    admin_headers = get_auth_headers(client, "desc_search@example.com", STRONG_PASSWORD, is_admin=True)

    # Create a book with specific description
    create_test_book(
        client,
        title="Generic Title",
        isbn="9781111111104",
        published_date="2023-01-15",
        description="This book covers machine learning fundamentals",
        admin_headers=admin_headers
    )

    # Search for "machine learning"
    response = client.get("/api/v1/books?search=machine%20learning")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] >= 1


def test_filter_by_author_id(client):
    """Test filtering books by author ID."""
    admin_headers = get_auth_headers(client, "author_filter@example.com", STRONG_PASSWORD, is_admin=True)

    # Create an author
    author = create_test_author(client, "Filter Author", admin_headers=admin_headers)
    author_id = author["id"]

    # Create books with and without the specific author
    create_test_book(
        client,
        title="Book With Author",
        isbn="9781111111105",
        published_date="2023-01-15",
        author_ids=[author_id],
        admin_headers=admin_headers
    )

    # Create another author for the second book
    other_author = create_test_author(client, "Unknown Author", admin_headers=admin_headers)
    create_test_book(
        client,
        title="Book Without Author",
        isbn="9781111111106",
        published_date="2023-01-15",
        author_ids=[other_author["id"]],
        admin_headers=admin_headers
    )

    # Filter by author_id
    response = client.get(f"/api/v1/books?author_id={author_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] >= 1
    for item in data["items"]:
        # Check that author_id is in the authors list
        author_ids = [author["id"] for author in item["authors"]]
        assert author_id in author_ids


def test_filter_by_category(client):
    """Test filtering books by category name."""
    admin_headers = get_auth_headers(client, "cat_filter@example.com", STRONG_PASSWORD, is_admin=True)

    # Create a category
    category = create_test_category(client, "Science Fiction", admin_headers=admin_headers)
    cat_id = category["id"]

    # Create a book and assign category
    book = create_test_book(
        client,
        title="Sci-Fi Book",
        isbn="9781111111107",
        published_date="2023-01-15",
        category_ids=[cat_id],
        admin_headers=admin_headers
    )

    # Filter by category name
    response = client.get("/api/v1/books?category=Science%20Fiction")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] >= 1


def test_filter_by_min_rating(client):
    """Test filtering books by minimum average rating."""
    # Create book owner (admin to create books)
    admin_headers = get_auth_headers(client, "rating_filter_owner@example.com", STRONG_PASSWORD, is_admin=True)

    # Create two books
    book1 = create_test_book(
        client,
        title="High Rated Book",
        isbn="9781111111108",
        published_date="2023-01-15",
        admin_headers=admin_headers
    )
    book2 = create_test_book(
        client,
        title="Low Rated Book",
        isbn="9781111111109",
        published_date="2023-01-15",
        admin_headers=admin_headers
    )

    book1_id = book1["id"]
    book2_id = book2["id"]

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
    admin_headers = get_auth_headers(client, "combined_filter@example.com", STRONG_PASSWORD, is_admin=True)

    # Create an author
    author = create_test_author(client, "Combined Author", admin_headers=admin_headers)
    author_id = author["id"]

    # Create a category
    category = create_test_category(client, "Combined Category", admin_headers=admin_headers)
    cat_id = category["id"]

    # Create a book with author, category, and searchable title
    create_test_book(
        client,
        title="Combined Filter Test",
        isbn="9781111111110",
        published_date="2023-01-15",
        author_ids=[author_id],
        category_ids=[cat_id],
        admin_headers=admin_headers
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
    admin_headers = get_auth_headers(client, "cat_response@example.com", STRONG_PASSWORD, is_admin=True)

    # Create a category
    category = create_test_category(client, "Response Test", admin_headers=admin_headers)
    cat_id = category["id"]

    # Create a book with category
    book = create_test_book(
        client,
        title="Category Response Book",
        isbn="9781111111111",
        published_date="2023-01-15",
        category_ids=[cat_id],
        admin_headers=admin_headers
    )
    book_id = book["id"]

    # Get single book
    response = client.get(f"/api/v1/books/{book_id}")
    assert response.status_code == 200

    data = response.json()
    assert "categories" in data
    assert len(data["categories"]) == 1
    assert data["categories"][0]["name"] == "Response Test"


def test_book_response_includes_average_rating(client):
    """Test that book response includes average rating."""
    # Create book as admin
    admin_headers = get_auth_headers(client, "avg_rating_owner@example.com", STRONG_PASSWORD, is_admin=True)

    # Create a book
    book = create_test_book(
        client,
        title="Rated Book",
        isbn="9781111111112",
        published_date="2023-01-15",
        admin_headers=admin_headers
    )
    book_id = book["id"]

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

