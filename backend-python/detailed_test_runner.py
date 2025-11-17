"""
Detailed CRUD Operations Test Runner
This script runs each CRUD operation test with detailed output.
"""
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import date

from src.main import app
from src.core.database import Base, get_db

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Create tables and setup
Base.metadata.create_all(bind=engine)
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

print("=" * 80)
print("BOOKS API - CRUD OPERATIONS TEST REPORT")
print("=" * 80)
print()

# Test 1: CREATE - Create a new book
print("=" * 80)
print("TEST 1: CREATE - Create a new book")
print("=" * 80)
book_data = {
    "title": "The Python Guide",
    "author": "John Doe",
    "isbn": "978-0123456789",
    "published_date": "2023-01-15",
    "description": "A comprehensive guide to Python programming"
}
print(f"Request: POST /books")
print(f"Payload: {book_data}")
response = client.post("/books", json=book_data)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
assert response.status_code == 201
created_book = response.json()
book_id_1 = created_book["id"]
print(f"✅ SUCCESS - Book created with ID: {book_id_1}")
print()

# Test 2: READ - Get all books
print("=" * 80)
print("TEST 2: READ - Get all books")
print("=" * 80)
print(f"Request: GET /books")
response = client.get("/books")
print(f"Status Code: {response.status_code}")
books_list = response.json()
print(f"Response: Found {len(books_list)} book(s)")
for book in books_list:
    print(f"  - ID: {book['id']}, Title: {book['title']}, Author: {book['author']}")
assert response.status_code == 200
assert len(books_list) >= 1
print(f"✅ SUCCESS - Retrieved all books")
print()

# Test 3: READ - Get book by ID
print("=" * 80)
print("TEST 3: READ - Get book by ID")
print("=" * 80)
print(f"Request: GET /books/{book_id_1}")
response = client.get(f"/books/{book_id_1}")
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
assert response.status_code == 200
retrieved_book = response.json()
assert retrieved_book["id"] == book_id_1
assert retrieved_book["title"] == book_data["title"]
print(f"✅ SUCCESS - Retrieved book with ID {book_id_1}")
print()

# Test 4: UPDATE - Update a book (partial update)
print("=" * 80)
print("TEST 4: UPDATE - Update a book (partial update)")
print("=" * 80)
update_data = {
    "title": "The Advanced Python Guide",
    "description": "An updated comprehensive guide to Python programming"
}
print(f"Request: PUT /books/{book_id_1}")
print(f"Payload: {update_data}")
response = client.put(f"/books/{book_id_1}", json=update_data)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
assert response.status_code == 200
updated_book = response.json()
assert updated_book["title"] == "The Advanced Python Guide"
assert updated_book["author"] == "John Doe"  # Should remain unchanged
print(f"✅ SUCCESS - Book {book_id_1} updated successfully")
print()

# Test 5: CREATE - Create another book
print("=" * 80)
print("TEST 5: CREATE - Create another book")
print("=" * 80)
book_data_2 = {
    "title": "FastAPI in Action",
    "author": "Jane Smith",
    "isbn": "978-9876543210",
    "published_date": "2023-06-20",
    "description": "Building modern APIs with FastAPI"
}
print(f"Request: POST /books")
print(f"Payload: {book_data_2}")
response = client.post("/books", json=book_data_2)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
assert response.status_code == 201
book_id_2 = response.json()["id"]
print(f"✅ SUCCESS - Book created with ID: {book_id_2}")
print()

# Test 6: READ - Get all books (should now have 2 books)
print("=" * 80)
print("TEST 6: READ - Get all books (should have multiple books)")
print("=" * 80)
print(f"Request: GET /books")
response = client.get("/books")
print(f"Status Code: {response.status_code}")
books_list = response.json()
print(f"Response: Found {len(books_list)} book(s)")
for book in books_list:
    print(f"  - ID: {book['id']}, Title: {book['title']}, Author: {book['author']}")
assert response.status_code == 200
assert len(books_list) == 2
print(f"✅ SUCCESS - Retrieved all {len(books_list)} books")
print()

# Test 7: DELETE - Delete a book
print("=" * 80)
print("TEST 7: DELETE - Delete a book")
print("=" * 80)
print(f"Request: DELETE /books/{book_id_2}")
response = client.delete(f"/books/{book_id_2}")
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
assert response.status_code == 200
assert response.json() == {"message": "Book deleted successfully"}
print(f"✅ SUCCESS - Book {book_id_2} deleted successfully")
print()

# Test 8: READ - Verify book is deleted (should return 404)
print("=" * 80)
print("TEST 8: READ - Verify deleted book returns 404")
print("=" * 80)
print(f"Request: GET /books/{book_id_2}")
response = client.get(f"/books/{book_id_2}")
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
assert response.status_code == 404
print(f"✅ SUCCESS - Book {book_id_2} not found (as expected)")
print()

# Test 9: Error handling - Try to create duplicate ISBN
print("=" * 80)
print("TEST 9: ERROR HANDLING - Duplicate ISBN")
print("=" * 80)
duplicate_book = {
    "title": "Another Book",
    "author": "Another Author",
    "isbn": "978-0123456789",  # Same as first book
    "published_date": "2023-01-15",
    "description": "Should fail"
}
print(f"Request: POST /books")
print(f"Payload: {duplicate_book}")
response = client.post("/books", json=duplicate_book)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
assert response.status_code == 400
assert "already exists" in response.json()["detail"]
print(f"✅ SUCCESS - Duplicate ISBN properly rejected")
print()

# Test 10: Error handling - Update non-existent book
print("=" * 80)
print("TEST 10: ERROR HANDLING - Update non-existent book")
print("=" * 80)
print(f"Request: PUT /books/99999")
print(f"Payload: {{'title': 'New Title'}}")
response = client.put("/books/99999", json={"title": "New Title"})
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
assert response.status_code == 404
print(f"✅ SUCCESS - Non-existent book update properly rejected")
print()

# Test 11: Error handling - Delete non-existent book
print("=" * 80)
print("TEST 11: ERROR HANDLING - Delete non-existent book")
print("=" * 80)
print(f"Request: DELETE /books/99999")
response = client.delete("/books/99999")
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
assert response.status_code == 404
print(f"✅ SUCCESS - Non-existent book delete properly rejected")
print()

# Test 12: UPDATE - Full update with all fields
print("=" * 80)
print("TEST 12: UPDATE - Full update with all fields")
print("=" * 80)
full_update = {
    "title": "The Complete Python Guide - Third Edition",
    "author": "John Doe and Contributors",
    "isbn": "978-1111111111",
    "published_date": "2024-01-01",
    "description": "The most comprehensive Python guide available"
}
print(f"Request: PUT /books/{book_id_1}")
print(f"Payload: {full_update}")
response = client.put(f"/books/{book_id_1}", json=full_update)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
assert response.status_code == 200
updated_book = response.json()
assert updated_book["title"] == full_update["title"]
assert updated_book["author"] == full_update["author"]
assert updated_book["isbn"] == full_update["isbn"]
print(f"✅ SUCCESS - Book {book_id_1} fully updated")
print()

# Test 13: DELETE - Clean up remaining book
print("=" * 80)
print("TEST 13: DELETE - Clean up remaining book")
print("=" * 80)
print(f"Request: DELETE /books/{book_id_1}")
response = client.delete(f"/books/{book_id_1}")
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
assert response.status_code == 200
print(f"✅ SUCCESS - Book {book_id_1} deleted successfully")
print()

# Test 14: READ - Verify all books are deleted
print("=" * 80)
print("TEST 14: READ - Verify database is empty")
print("=" * 80)
print(f"Request: GET /books")
response = client.get("/books")
print(f"Status Code: {response.status_code}")
books_list = response.json()
print(f"Response: Found {len(books_list)} book(s)")
assert response.status_code == 200
assert len(books_list) == 0
print(f"✅ SUCCESS - All books deleted, database is clean")
print()

# Final Summary
print("=" * 80)
print("SUMMARY - ALL CRUD OPERATIONS TESTED SUCCESSFULLY")
print("=" * 80)
print("✅ CREATE Operations: 2 tests passed")
print("✅ READ Operations: 5 tests passed")
print("✅ UPDATE Operations: 2 tests passed")
print("✅ DELETE Operations: 2 tests passed")
print("✅ ERROR HANDLING: 3 tests passed")
print("=" * 80)
print("Total: 14/14 tests passed")
print("=" * 80)

