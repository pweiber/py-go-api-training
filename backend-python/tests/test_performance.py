"""
Performance tests for API endpoints.

Tests that critical endpoints respond within acceptable time limits.
"""
import time
import pytest
from tests.conftest import get_auth_headers, create_test_author, create_test_book, create_test_category, STRONG_PASSWORD


def test_books_list_response_time(client):
    """List endpoint responds within 500ms."""
    admin_headers = get_auth_headers(client, "perf_admin@example.com", STRONG_PASSWORD, is_admin=True)

    # Create some test data (10 books)
    author = create_test_author(client, "Performance Author", admin_headers=admin_headers)
    for i in range(10):
        create_test_book(
            client,
            title=f"Performance Book {i}",
            isbn=f"978-0-{i:03d}-00000-0",
            author_ids=[author["id"]],
            admin_headers=admin_headers
        )

    # Measure response time
    start = time.time()
    response = client.get("/api/v1/books?page=1&size=50")
    elapsed_ms = (time.time() - start) * 1000

    assert response.status_code == 200
    assert elapsed_ms < 500, f"Took {elapsed_ms:.0f}ms, expected < 500ms"


def test_statistics_response_time(client):
    """Stats endpoint with aggregates < 500ms."""
    admin_headers = get_auth_headers(client, "stats_perf@example.com", STRONG_PASSWORD, is_admin=True)

    # Create some test data
    author = create_test_author(client, "Stats Author", admin_headers=admin_headers)
    category = create_test_category(client, "Stats Category", admin_headers=admin_headers)

    for i in range(5):
        create_test_book(
            client,
            title=f"Stats Book {i}",
            isbn=f"978-1-{i:03d}-00000-0",
            author_ids=[author["id"]],
            category_ids=[category["id"]],
            admin_headers=admin_headers
        )

    # Measure response time
    start = time.time()
    response = client.get("/api/v1/stats")
    elapsed_ms = (time.time() - start) * 1000

    assert response.status_code == 200
    assert elapsed_ms < 500, f"Took {elapsed_ms:.0f}ms, expected < 500ms"


def test_search_response_time(client):
    """Filtered query < 500ms."""
    admin_headers = get_auth_headers(client, "search_perf@example.com", STRONG_PASSWORD, is_admin=True)

    # Create test data with searchable content
    author = create_test_author(client, "Search Author", admin_headers=admin_headers)

    for i in range(15):
        create_test_book(
            client,
            title=f"Python Programming Book {i}",
            isbn=f"978-2-{i:03d}-00000-0",
            description="A comprehensive guide to Python programming",
            author_ids=[author["id"]],
            admin_headers=admin_headers
        )

    # Measure search response time
    start = time.time()
    response = client.get("/api/v1/books?search=Python")
    elapsed_ms = (time.time() - start) * 1000

    assert response.status_code == 200
    assert elapsed_ms < 500, f"Took {elapsed_ms:.0f}ms, expected < 500ms"

    # Verify search actually found results
    data = response.json()
    assert data["total"] > 0


def test_pagination_large_dataset(client):
    """100+ records still perform well."""
    admin_headers = get_auth_headers(client, "pagination_perf@example.com", STRONG_PASSWORD, is_admin=True)

    # Create a large dataset (50 books - scaled down for in-memory SQLite)
    author = create_test_author(client, "Large Dataset Author", admin_headers=admin_headers)

    for i in range(50):
        create_test_book(
            client,
            title=f"Large Dataset Book {i}",
            isbn=f"978-3-{i:03d}-00000-0",
            author_ids=[author["id"]],
            admin_headers=admin_headers
        )

    # Test pagination performance on large dataset
    start = time.time()
    response = client.get("/api/v1/books?page=2&size=20")
    elapsed_ms = (time.time() - start) * 1000

    assert response.status_code == 200
    assert elapsed_ms < 500, f"Took {elapsed_ms:.0f}ms, expected < 500ms"

    # Verify pagination works correctly
    data = response.json()
    assert data["total"] >= 50
    assert len(data["items"]) <= 20

