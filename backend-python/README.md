# Backend Python - FastAPI Training Project

This is a production-ready FastAPI backend structure for the intern training program. Follow the tasks in the main `task_based_junior_developer_program.md` to progressively build your API.

## 📁 Folder Structure

```
backend-python/
├── src/                          # Source code
│   ├── api/                      # API layer
│   │   └── v1/                   # API version 1
│   │       └── endpoints/        # API endpoint modules (routes)
│   ├── core/                     # Core application modules
│   │   ├── config.py            # Configuration management
│   │   └── database.py          # Database connection
│   ├── models/                   # SQLAlchemy database models
│   ├── schemas/                  # Pydantic schemas (request/response)
│   ├── services/                 # Business logic layer
│   ├── repositories/             # Data access layer
│   ├── grpc/                     # gRPC services (advanced)
│   └── main.py                   # Application entry point
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── conftest.py              # Pytest configuration
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Development dependencies
├── Dockerfile                    # Docker container definition
├── docker-compose.yml           # Multi-container setup
├── .env.example                 # Environment variables template
├── pytest.ini                   # Pytest configuration
└── README.md                    # This file
```

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 13+
- Docker & Docker Compose (optional but recommended)

### Setup Instructions

#### Option 1: Using Docker (Recommended)

1. **Copy environment variables:**
   ```bash
   cp .env.example .env
   ```

2. **Start the services:**
   ```bash
   docker-compose up -d
   ```

3. **Access the API:**
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

#### Option 2: Local Development

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

4. **Start PostgreSQL:**
   ```bash
   # Using Docker
   docker run --name postgres-dev \
     -e POSTGRES_PASSWORD=devpassword \
     -e POSTGRES_DB=bookstore \
     -p 5432:5432 -d postgres:15
   ```

5. **Run the application:**
   ```bash
   uvicorn src.main:app --reload
   ```

### Database Migrations

This project uses [Alembic](https://alembic.sqlalchemy.org/) for database migrations.

1. **Initialize/Upgrade database:**
   ```bash
   alembic upgrade head
   ```

2. **Create a new migration:**
   ```bash
   alembic revision --autogenerate -m "Description of changes"
   ```

## 🌐 API Endpoints

### API Versioning

This API uses URL-based versioning with the `/api/v1` prefix for all endpoints. This approach:
- Provides clear API version identification
- Allows for future versions (v2, v3) without breaking existing clients
- Aligns URL structure with the directory structure (`src/api/v1/`)
- Follows REST API industry best practices

### Available Endpoints

#### Books API (v1)

All book endpoints are prefixed with `/api/v1/books`:

- **GET** `/api/v1/books` - List all books
- **POST** `/api/v1/books` - Create a new book
- **GET** `/api/v1/books/{id}` - Get a specific book by ID
- **PUT** `/api/v1/books/{id}` - Update a book
- **DELETE** `/api/v1/books/{id}` - Delete a book

#### System Endpoints

- **GET** `/` - API root and information
- **GET** `/health` - Health check endpoint
- **GET** `/docs` - Interactive API documentation (Swagger UI)
- **GET** `/redoc` - Alternative API documentation (ReDoc)

### Example API Calls

```bash
# Create a book
curl -X POST "http://localhost:8000/api/v1/books" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "The Python Guide",
    "author": "John Doe",
    "isbn": "978-0123456789",
    "published_date": "2023-01-15",
    "description": "A comprehensive guide to Python"
  }'

# Get all books
curl -X GET "http://localhost:8000/api/v1/books"

# Get a specific book
curl -X GET "http://localhost:8000/api/v1/books/1"

# Update a book
curl -X PUT "http://localhost:8000/api/v1/books/1" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "The Advanced Python Guide",
    "description": "An advanced guide with best practices"
  }'

# Delete a book
curl -X DELETE "http://localhost:8000/api/v1/books/1"
```

## 📝 Development Workflow

### Adding New Features

Follow this pattern when implementing tasks:

1. **Create Model** (`src/models/`)
   - Define SQLAlchemy model
   - Add relationships

2. **Create Schema** (`src/schemas/`)
   - Define Pydantic models for validation
   - Create request/response schemas

3. **Create Repository** (`src/repositories/`)
   - Implement data access methods
   - Handle database queries

4. **Create Service** (`src/services/`)
   - Implement business logic
   - Use repositories for data access

5. **Create Endpoint** (`src/api/v1/endpoints/`)
   - Define API routes
   - Use services for business logic
   - Add proper error handling

6. **Write Tests** (`tests/`)
   - Unit tests for services
   - Integration tests for endpoints

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_example.py

# Run tests by marker
pytest -m unit
pytest -m integration
```

### Code Quality

```bash
# Format code
black src tests

# Sort imports
isort src tests

# Lint code
flake8 src tests
pylint src

# Type checking
mypy src
```

## 🎯 Task Implementation Guide

### Task 1: Basic REST API Setup
- Create `Book` model in `src/models/book.py`
- Create schemas in `src/schemas/book.py`
- Create endpoints in `src/api/v1/endpoints/books.py`
- Update `src/main.py` to include the router

### Task 2: Authentication & User Management
- Create `User` model in `src/models/user.py`
- Implement authentication in `src/core/security.py`
- Create auth endpoints in `src/api/v1/endpoints/auth.py`
- Add authentication dependencies

### Task 3: CRUD Operations with Relationships
- Extend models with relationships
- Create repository pattern implementations
- Add filtering and pagination
- Implement complex queries

### Task 4: API Testing & Validation
- Write comprehensive unit tests
- Create integration tests
- Add input validation
- Test error scenarios

## 📚 Key Concepts

### Architecture Layers

1. **API Layer** (`api/`): HTTP endpoints, request/response handling
2. **Service Layer** (`services/`): Business logic, orchestration
3. **Repository Layer** (`repositories/`): Data access, database queries
4. **Model Layer** (`models/`): Database schema definitions
5. **Schema Layer** (`schemas/`): Data validation, serialization

### Best Practices

- ✅ Use dependency injection for database sessions
- ✅ Validate all inputs with Pydantic schemas
- ✅ Handle errors gracefully with proper HTTP status codes
- ✅ Write tests for all endpoints and business logic
- ✅ Use environment variables for configuration
- ✅ Follow RESTful API conventions
- ✅ Document your code and APIs
- ✅ Use type hints throughout your code

## 🔧 Troubleshooting

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# View PostgreSQL logs
docker logs postgres-dev

# Test connection
psql -h localhost -U postgres -d bookstore
```

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

## 📖 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Pytest Documentation](https://docs.pytest.org/)

