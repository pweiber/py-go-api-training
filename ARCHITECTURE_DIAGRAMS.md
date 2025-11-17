# Architecture Visualization - py-go-api-training

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Browser    │  │   Postman    │  │  Mobile App  │              │
│  │  (Frontend)  │  │ (Collection) │  │   (Future)   │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                  │                  │                       │
│         └──────────────────┴──────────────────┘                       │
│                            │                                          │
│                       HTTP/HTTPS                                      │
│                            │                                          │
└────────────────────────────┼──────────────────────────────────────────┘
                             │
┌────────────────────────────┼──────────────────────────────────────────┐
│                   PRESENTATION LAYER                                  │
├────────────────────────────┼──────────────────────────────────────────┤
│                            ▼                                          │
│   ┌─────────────────────────────────────────────────────────┐        │
│   │           FastAPI Application (main.py)                  │        │
│   │  • CORS Middleware                                       │        │
│   │  • Exception Handlers                                    │        │
│   │  • API Documentation (Swagger/ReDoc)                     │        │
│   │  • Health Check Endpoints                                │        │
│   └────────────────────┬────────────────────────────────────┘        │
│                        │                                              │
│                        ▼                                              │
│   ┌─────────────────────────────────────────────────────────┐        │
│   │              API Router (v1)                             │        │
│   │  /books - Book endpoints                                 │        │
│   │  /authors - Author endpoints (future)                    │        │
│   │  /categories - Category endpoints (future)               │        │
│   │  /reviews - Review endpoints (future)                    │        │
│   └────────────────────┬────────────────────────────────────┘        │
│                        │                                              │
└────────────────────────┼──────────────────────────────────────────────┘
                         │
┌────────────────────────┼──────────────────────────────────────────────┐
│                   API ENDPOINTS LAYER                                 │
├────────────────────────┼──────────────────────────────────────────────┤
│                        ▼                                              │
│   ┌──────────────────────────────────────────────────────┐           │
│   │         books.py - REST API Endpoints                │           │
│   │                                                       │           │
│   │  GET    /books         → get_books()                │           │
│   │  GET    /books/{id}    → get_book()                 │           │
│   │  POST   /books         → create_book()              │           │
│   │  PUT    /books/{id}    → update_book()              │           │
│   │  DELETE /books/{id}    → delete_book()              │           │
│   │                                                       │           │
│   │  • Async endpoint handlers                           │           │
│   │  • Pydantic schema validation                        │           │
│   │  • HTTP exception handling                           │           │
│   │  • Database session injection                        │           │
│   └───────────────────────┬──────────────────────────────┘           │
│                           │                                           │
└───────────────────────────┼───────────────────────────────────────────┘
                            │
      ┌─────────────────────┼─────────────────────┐
      │                     │                     │
      ▼                     ▼                     ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  Services   │      │Repositories │      │Direct DB    │
│  (Future)   │      │  (Future)   │      │Access (Now) │
│             │      │             │      │             │
│  Business   │      │  Data       │      │  SQLAlchemy │
│  Logic      │      │  Access     │      │  Queries    │
└─────────────┘      └─────────────┘      └──────┬──────┘
                                                  │
┌─────────────────────────────────────────────────┼──────────────────────┐
│                   DATA ACCESS LAYER             │                      │
├─────────────────────────────────────────────────┼──────────────────────┤
│                                                 ▼                      │
│   ┌──────────────────────────────────────────────────────┐            │
│   │          SQLAlchemy Session Management               │            │
│   │  • Connection Pool (size=10, overflow=20)            │            │
│   │  • Session Factory (SessionLocal)                    │            │
│   │  • Dependency Injection (get_db)                     │            │
│   │  • Transaction Management                            │            │
│   │  • Connection Health Checks                          │            │
│   └──────────────────────────┬───────────────────────────┘            │
│                              │                                         │
│                              ▼                                         │
│   ┌──────────────────────────────────────────────────────┐            │
│   │              ORM Models (models/)                    │            │
│   │                                                       │            │
│   │  Book Model:                                         │            │
│   │  • id: Integer (PK)                                  │            │
│   │  • title: String(255)                                │            │
│   │  • author: String(255)                               │            │
│   │  • isbn: String(13) [UNIQUE]                         │            │
│   │  • published_date: Date                              │            │
│   │  • description: Text                                 │            │
│   │                                                       │            │
│   │  Indexes: id, title, isbn                            │            │
│   └──────────────────────────┬───────────────────────────┘            │
│                              │                                         │
└──────────────────────────────┼─────────────────────────────────────────┘
                               │
┌──────────────────────────────┼─────────────────────────────────────────┐
│                       DATABASE LAYER                                   │
├──────────────────────────────┼─────────────────────────────────────────┤
│                              ▼                                         │
│   ┌────────────────────────────────────────────────┐                  │
│   │         PostgreSQL Database                     │                  │
│   │                                                 │                  │
│   │  Table: books                                   │                  │
│   │  ┌─────────────────────────────────────┐       │                  │
│   │  │ id | title | author | isbn | ...   │       │                  │
│   │  ├─────────────────────────────────────┤       │                  │
│   │  │  1 | Python | John  | 978... | ... │       │                  │
│   │  │  2 | FastAPI| Jane  | 979... | ... │       │                  │
│   │  └─────────────────────────────────────┘       │                  │
│   │                                                 │                  │
│   │  • ACID Transactions                            │                  │
│   │  • Constraints (UNIQUE, NOT NULL)               │                  │
│   │  • Indexes for Performance                      │                  │
│   └────────────────────────────────────────────────┘                  │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────┐
│                      VALIDATION LAYER                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   ┌──────────────────────────────────────────────────────┐          │
│   │       Pydantic Schemas (schemas/)                    │          │
│   │                                                       │          │
│   │  BookBase:                                           │          │
│   │  • title: str (1-255 chars)                          │          │
│   │  • author: str (1-255 chars)                         │          │
│   │  • isbn: str (10-13 chars)                           │          │
│   │  • published_date: date                              │          │
│   │  • description: Optional[str]                        │          │
│   │                                                       │          │
│   │  BookCreate(BookBase) - For POST requests            │          │
│   │  BookUpdate(BaseModel) - For PUT requests            │          │
│   │  BookResponse(BookBase) - For responses              │          │
│   │                                                       │          │
│   │  • Runtime validation                                │          │
│   │  • Type coercion                                     │          │
│   │  • Custom validators                                 │          │
│   │  • JSON schema generation                            │          │
│   └──────────────────────────────────────────────────────┘          │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────┐
│                   CONFIGURATION LAYER                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   ┌──────────────────────────────────────────────────────┐          │
│   │          Settings (core/config.py)                   │          │
│   │                                                       │          │
│   │  Environment Variables:                              │          │
│   │  • DATABASE_URL                                      │          │
│   │  • SECRET_KEY                                        │          │
│   │  • ALLOWED_ORIGINS                                   │          │
│   │  • REDIS_URL                                         │          │
│   │  • LOG_LEVEL                                         │          │
│   │                                                       │          │
│   │  Using: pydantic-settings                            │          │
│   │  Source: .env file or environment                    │          │
│   └──────────────────────────────────────────────────────┘          │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

## Request Flow Diagram

```
┌──────────┐
│  Client  │
└────┬─────┘
     │
     │ 1. HTTP POST /books
     │    {title, author, isbn, ...}
     │
     ▼
┌─────────────────────┐
│   FastAPI Router    │
│   (CORS, Logging)   │
└─────────┬───────────┘
          │
          │ 2. Route to books.create_book()
          │
          ▼
┌──────────────────────────┐
│  Pydantic Validation     │
│  (BookCreate schema)     │
└─────────┬────────────────┘
          │
          │ 3. Validation passed
          │
          ▼
┌──────────────────────────┐
│  Endpoint Handler        │
│  async def create_book() │
└─────────┬────────────────┘
          │
          │ 4. Inject DB session
          │    db: Session = Depends(get_db)
          │
          ▼
┌──────────────────────────┐
│  Business Logic          │
│  • Check ISBN uniqueness │
│  • Create Book instance  │
└─────────┬────────────────┘
          │
          │ 5. SQLAlchemy ORM
          │    db.add(book)
          │    db.commit()
          │
          ▼
┌──────────────────────────┐
│   PostgreSQL Database    │
│   INSERT INTO books...   │
└─────────┬────────────────┘
          │
          │ 6. Return inserted row
          │
          ▼
┌──────────────────────────┐
│  Response Serialization  │
│  (BookResponse schema)   │
└─────────┬────────────────┘
          │
          │ 7. HTTP 201 Created
          │    {id, title, author, ...}
          │
          ▼
┌──────────┐
│  Client  │
└──────────┘
```

## Error Handling Flow

```
┌──────────┐
│  Client  │
└────┬─────┘
     │
     │ POST /books (with duplicate ISBN)
     │
     ▼
┌─────────────────────┐
│   Endpoint          │
└─────────┬───────────┘
          │
          │ Check if ISBN exists
          │
          ▼
┌──────────────────────────┐
│  db.query(Book)          │
│    .filter(isbn=isbn)    │
│    .first()              │
└─────────┬────────────────┘
          │
          │ Book found (duplicate)
          │
          ▼
┌──────────────────────────┐
│  raise HTTPException     │
│  status_code=400         │
│  detail="ISBN exists"    │
└─────────┬────────────────┘
          │
          │ FastAPI catches exception
          │
          ▼
┌──────────────────────────┐
│  HTTP 400 Response       │
│  {"detail": "..."}       │
└─────────┬────────────────┘
          │
          ▼
┌──────────┐
│  Client  │
│  (Error) │
└──────────┘
```

## Database Connection Pool

```
┌────────────────────────────────────────────────┐
│           Connection Pool                      │
│                                                │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐      │
│  │ Conn │  │ Conn │  │ Conn │  │ Conn │ ... │
│  │  1   │  │  2   │  │  3   │  │  10  │      │
│  └───┬──┘  └───┬──┘  └───┬──┘  └───┬──┘      │
│      │FREE     │BUSY     │FREE     │FREE      │
└──────┼─────────┼─────────┼─────────┼──────────┘
       │         │         │         │
       │         │         │         │
Request 1 ───────┘         │         │
Request 2 ─────────────────┘         │
Request 3 ───────────────────────────┘

Pool Configuration:
• pool_size = 10 (normal connections)
• max_overflow = 20 (burst capacity)
• pool_pre_ping = True (health check)
• pool_recycle = 3600 (recycle after 1hr)
```

## Testing Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Test Suite                           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────────────────────────────┐          │
│  │        Unit Tests (11 tests)             │          │
│  │                                           │          │
│  │  • test_health_check                     │          │
│  │  • test_create_book                      │          │
│  │  • test_create_book_duplicate_isbn       │          │
│  │  • test_get_all_books                    │          │
│  │  • test_get_book_by_id                   │          │
│  │  • test_get_book_by_id_not_found         │          │
│  │  • test_update_book                      │          │
│  │  • test_update_book_not_found            │          │
│  │  • test_delete_book                      │          │
│  │  • test_delete_book_not_found            │          │
│  │                                           │          │
│  │  Focus: Individual endpoint testing      │          │
│  │  Isolation: Each test creates own data   │          │
│  └──────────────────────────────────────────┘          │
│                                                          │
│  ┌──────────────────────────────────────────┐          │
│  │    Integration Tests (5 workflows)       │          │
│  │                                           │          │
│  │  • test_complete_crud_workflow           │          │
│  │  • test_multiple_books_management        │          │
│  │  • test_error_handling_workflow          │          │
│  │  • test_partial_update_workflow          │          │
│  │                                           │          │
│  │  Focus: End-to-end user scenarios        │          │
│  │  Coverage: Multiple operations chained   │          │
│  └──────────────────────────────────────────┘          │
│                                                          │
│  ┌──────────────────────────────────────────┐          │
│  │         Test Fixtures (conftest.py)      │          │
│  │                                           │          │
│  │  [EMPTY - NEEDS IMPLEMENTATION]          │          │
│  │                                           │          │
│  │  Planned:                                 │          │
│  │  • @pytest.fixture def client()          │          │
│  │  • @pytest.fixture def test_db()         │          │
│  │  • Database setup/teardown               │          │
│  └──────────────────────────────────────────┘          │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## Docker Container Architecture

```
┌───────────────────────────────────────────────────────────┐
│                   Docker Container                        │
├───────────────────────────────────────────────────────────┤
│                                                            │
│  ┌─────────────────────────────────────────────────┐     │
│  │  Multi-Stage Build Process                      │     │
│  │                                                  │     │
│  │  Stage 1: Builder                                │     │
│  │  ┌──────────────────────────────────────┐       │     │
│  │  │ • python:3.11-slim                   │       │     │
│  │  │ • Install gcc, build tools           │       │     │
│  │  │ • pip install requirements           │       │     │
│  │  │ • Output: /root/.local packages      │       │     │
│  │  └──────────────────────────────────────┘       │     │
│  │              │                                   │     │
│  │              │ Copy packages only                │     │
│  │              ▼                                   │     │
│  │  Stage 2: Runtime                                │     │
│  │  ┌──────────────────────────────────────┐       │     │
│  │  │ • python:3.11-slim                   │       │     │
│  │  │ • Copy packages from builder         │       │     │
│  │  │ • Create non-root user (appuser)     │       │     │
│  │  │ • Copy application code              │       │     │
│  │  │ • No build tools (secure)            │       │     │
│  │  └──────────────────────────────────────┘       │     │
│  └─────────────────────────────────────────────────┘     │
│                                                            │
│  Running Container:                                        │
│  ┌─────────────────────────────────────────────────┐     │
│  │  User: appuser (UID 1000) ← Security            │     │
│  │  Port: 8000 ← Exposed                            │     │
│  │  Health Check: GET /health ← Monitoring          │     │
│  │  Command: uvicorn src.main:app                   │     │
│  │  Volume: ./src → /app/src ← Hot reload           │     │
│  └─────────────────────────────────────────────────┘     │
│                                                            │
└────────────────────────────────────────────────────────────┘
              │
              │ Network: bridge
              │
              ▼
    ┌──────────────────┐
    │  host.docker.    │
    │  internal:5432   │ ← Local PostgreSQL
    └──────────────────┘
```

## Deployment Architecture (Production)

```
┌─────────────────────────────────────────────────────────────┐
│                      Load Balancer                          │
│                    (NGINX/AWS ALB)                           │
└───────────────┬──────────────┬──────────────┬───────────────┘
                │              │              │
                ▼              ▼              ▼
        ┌───────────┐  ┌───────────┐  ┌───────────┐
        │  FastAPI  │  │  FastAPI  │  │  FastAPI  │
        │Container 1│  │Container 2│  │Container 3│
        └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
              │              │              │
              └──────────────┴──────────────┘
                            │
                            ▼
              ┌──────────────────────────┐
              │   PostgreSQL Cluster     │
              │   (Primary + Replicas)   │
              └──────────────────────────┘
                            │
                            ▼
              ┌──────────────────────────┐
              │    Redis Cache           │
              │   (Session, Cache)       │
              └──────────────────────────┘
```

---

## Key Architectural Decisions

### ✅ What's Implemented
1. **Layered Architecture** - Clean separation of concerns
2. **Async/Await** - Non-blocking I/O for scalability
3. **Connection Pooling** - Efficient database connections
4. **Schema Validation** - Pydantic for type safety
5. **Dependency Injection** - FastAPI's DI container
6. **Docker Support** - Containerized deployment
7. **Health Checks** - Monitoring endpoints
8. **CORS Middleware** - Cross-origin support

### ⚠️ Planned Improvements
1. **Service Layer** - Business logic separation
2. **Repository Pattern** - Data access abstraction
3. **Caching Layer** - Redis integration
4. **Authentication** - JWT implementation
5. **Logging** - Structured logging
6. **Monitoring** - Metrics and traces
7. **Database Migrations** - Alembic setup
8. **CI/CD Pipeline** - Automated deployment

---

**This visualization represents the current state (Task 1) and planned architecture for the py-go-api-training repository.**

