from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.core.database import Base, get_db

# Create in-memory SQLite database for testing
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

# Create tables
Base.metadata.create_all(bind=engine)

# Override the dependency
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

book_data = {
    'title': 'The Python Guide',
    'author': 'John Doe',
    'isbn': '978-0123456789',
    'published_date': '2023-01-15',
    'description': 'A comprehensive guide to Python programming'
}
response = client.post('/books', json=book_data)
print('Status:', response.status_code)
print('Response:', response.json())

