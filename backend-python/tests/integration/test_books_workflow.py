"""
Integration tests for the complete Books API workflow.
Updated to work with new security model where:
- Registration always creates USER role
- Users can only update/delete their own books
"""
import pytest


# Strong password that meets all requirements
STRONG_PASSWORD = "TestPass123!"


def get_auth_headers(client, email, password):
    """Helper function to register, login, and get auth headers.
    Note: Registration always creates USER role (security fix).
    """
    client.post("/register", json={
        "email": email,
        "password": password
    })
    login_response = client.post("/login", json={
        "email": email,
        "password": password
    })
    token = login_response. json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_complete_crud_workflow(client):
    """
    Test complete CRUD workflow: Create -> Read -> Update -> Delete
    User creates and manages their own book.
    """
    # Get auth headers
    headers = get_auth_headers(client, "workflow@example.com", STRONG_PASSWORD)

    # Step 1: Create a book
    book_data = {
        "title": "Integration Test Book",
        "author": "Integration Author",
        "isbn": "978-5555555555",
        "published_date": "2023-06-15",
        "description": "Testing the complete workflow"
    }
    create_response = client. post("/books", json=book_data, headers=headers)
    assert create_response.status_code == 201
    created_book = create_response.json()
    book_id = created_book["id"]
    assert created_book["title"] == book_data["title"]

    # Step 2: Read the book by ID
    get_response = client. get(f"/books/{book_id}", headers=headers)
    assert get_response.status_code == 200
    retrieved_book = get_response.json()
    assert retrieved_book["id"] == book_id
    assert retrieved_book["title"] == book_data["title"]

    # Step 3: Read all books (should include our book)
    list_response = client. get("/books", headers=headers)
    assert list_response. status_code == 200
    books_list = list_response. json()
    assert any(book["id"] == book_id for book in books_list)

    # Step 4: Update the book (owner can update their own book)
    update_data = {
        "title": "Updated Integration Book",
        "description": "Updated description for integration test"
    }
    update_response = client.put(f"/books/{book_id}", json=update_data, headers=headers)
    assert update_response. status_code == 200
    updated_book = update_response.json()
    assert updated_book["title"] == "Updated Integration Book"
    assert updated_book["description"] == "Updated description for integration test"
    assert updated_book["author"] == book_data["author"]  # Unchanged

    # Step 5: Delete the book (owner can delete their own book)
    delete_response = client.delete(f"/books/{book_id}", headers=headers)
    assert delete_response.status_code == 200
    assert delete_response.json() == {"message": "Book deleted successfully"}

    # Step 6: Verify deletion
    verify_response = client. get(f"/books/{book_id}", headers=headers)
    assert verify_response.status_code == 404


def test_multiple_books_management(client):
    """
    Test managing multiple books simultaneously.
    Same user creates and manages all books.
    """
    # Get auth headers
    headers = get_auth_headers(client, "multibook@example.com", STRONG_PASSWORD)

    books_data = [
        {
            "title": "Book One",
            "author": "Author One",
            "isbn": "978-6666666666",
            "published_date": "2023-01-01",
            "description": "First book"
        },
        {
            "title": "Book Two",
            "author": "Author Two",
            "isbn": "978-7777777777",
            "published_date": "2023-02-01",
            "description": "Second book"
        },
        {
            "title": "Book Three",
            "author": "Author Three",
            "isbn": "978-8888888888",
            "published_date": "2023-03-01",
            "description": "Third book"
        }
    ]

    # Create multiple books
    created_ids = []
    for book_data in books_data:
        response = client.post("/books", json=book_data, headers=headers)
        assert response.status_code == 201
        created_ids.append(response. json()["id"])

    # Verify all books exist
    list_response = client. get("/books", headers=headers)
    assert list_response. status_code == 200
    books_list = list_response.json()
    assert len(books_list) >= 3

    for book_id in created_ids:
        assert any(book["id"] == book_id for book in books_list)

    # Update one book (owner can update their own)
    update_response = client.put(
        f"/books/{created_ids[1]}",
        json={"title": "Updated Book Two"},
        headers=headers
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Updated Book Two"

    # Delete all created books (owner can delete their own)
    for book_id in created_ids:
        delete_response = client.delete(f"/books/{book_id}", headers=headers)
        assert delete_response.status_code == 200


def test_error_handling_workflow(client):
    """
    Test various error scenarios in a workflow.
    """
    # Get auth headers for authenticated tests
    headers = get_auth_headers(client, "errortest@example.com", STRONG_PASSWORD)

    # Create a book first so we can test ownership-based errors
    book_data = {
        "title": "Error Test Book",
        "author": "Error Author",
        "isbn": "978-9999999999",
        "published_date": "2023-01-01",
        "description": "For error testing"
    }
    create_response = client.post("/books", json=book_data, headers=headers)
    assert create_response.status_code == 201
    book_id = create_response.json()["id"]

    # Try to get non-existent book
    response = client.get("/books/99999", headers=headers)
    assert response.status_code == 404

    # Try to update non-existent book
    response = client.put("/books/99999", json={"title": "Test"}, headers=headers)
    assert response.status_code == 404

    # Try to delete non-existent book
    response = client.delete("/books/99999", headers=headers)
    assert response.status_code == 404

    # Try to create duplicate ISBN
    duplicate_response = client.post("/books", json=book_data, headers=headers)
    assert duplicate_response.status_code == 400
    assert "already exists" in duplicate_response.json()["detail"]

    # Clean up (owner can delete their own)
    client.delete(f"/books/{book_id}", headers=headers)


def test_partial_update_workflow(client):
    """
    Test that partial updates work correctly and don't affect other fields.
    """
    # Get auth headers
    headers = get_auth_headers(client, "partial@example.com", STRONG_PASSWORD)

    # Create initial book
    book_data = {
        "title": "Original Title",
        "author": "Original Author",
        "isbn": "978-1010101010",
        "published_date": "2023-01-01",
        "description": "Original description"
    }
    create_response = client.post("/books", json=book_data, headers=headers)
    assert create_response.status_code == 201
    book_id = create_response. json()["id"]

    # Update only title (owner can update their own)
    response = client.put(f"/books/{book_id}", json={"title": "New Title"}, headers=headers)
    assert response.status_code == 200
    book = response.json()
    assert book["title"] == "New Title"
    assert book["author"] == "Original Author"
    assert book["description"] == "Original description"

    # Update only description
    response = client. put(f"/books/{book_id}", json={"description": "New description"}, headers=headers)
    assert response.status_code == 200
    book = response.json()
    assert book["title"] == "New Title"  # Previous update preserved
    assert book["description"] == "New description"

    # Update multiple fields
    response = client.put(
        f"/books/{book_id}",
        json={"author": "New Author", "title": "Final Title"},
        headers=headers
    )
    assert response. status_code == 200
    book = response.json()
    assert book["title"] == "Final Title"
    assert book["author"] == "New Author"
    assert book["description"] == "New description"  # Previous update preserved

    # Clean up (owner can delete their own)
    client. delete(f"/books/{book_id}", headers=headers)