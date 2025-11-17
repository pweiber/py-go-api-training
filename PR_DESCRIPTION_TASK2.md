## 🎯 Overview

This PR implements JWT-based authentication and role-based authorization for the Book Store API, building upon the foundation established in Task 1. Users can now register, login, and access protected endpoints with proper authentication tokens.

---

## 📝 Summary of Changes

### ✨ New Features

#### 1. User Management System

**User Model** (`src/models/user.py`)
- Complete user entity with email, hashed password, role, and timestamps
- Support for two roles: `user` and `admin`
- One-to-many relationship with books (creator tracking)

**User Schemas** (`src/schemas/user.py`)
- `UserCreate`: Registration with email, password validation, and role selection
- `UserLogin`: Login credentials schema
- `UserResponse`: Safe user data response (excludes password)
- `UserUpdate`: Profile update schema
- `Token`: JWT token response schema
- Password validation: minimum 8 characters, requires letters and digits

#### 2. Authentication System

**Core Authentication** (`src/core/auth.py`)

**Password Security**
- Bcrypt hashing using passlib

**JWT Token Management**
- Token generation with configurable expiration (default: 30 minutes)
- Token verification and validation
- Bearer token security scheme

**User Authentication**
- Email/password verification

**Authorization Dependencies**
- `get_current_user`: Validates JWT and returns authenticated user
- `get_admin_user`: Ensures user has admin role

**Authentication Endpoints** (`src/api/v1/endpoints/auth.py`)
- `POST /register`: User registration with role support
- `POST /login`: User authentication returning JWT token
- `GET /me`: Get current user profile
- `PUT /me`: Update current user profile

#### 3. Protected Book Endpoints

**Updated Books API** (`src/api/v1/endpoints/books.py`)
- `GET /books`: Public endpoint (no auth required)
- `GET /books/{id}`: Public endpoint (no auth required)
- `POST /books`: Protected endpoint (requires authentication)
  - Automatically tracks book creator via `created_by` field
- `PUT /books/{id}`: Public endpoint (as per Task 2 spec)
- `DELETE /books/{id}`: Admin-only endpoint (requires admin role)

#### 4. Database Migration

**Migration Script** (`migrate_task2.py`)
- Creates `users` table with proper indexes
- Adds `created_by` foreign key to `books` table
- Handles idempotent execution (safe to run multiple times)

#### 5. Configuration Updates

Added JWT configuration to `src/core/config.py`:
- `SECRET_KEY`: JWT signing secret
- `ALGORITHM`: JWT algorithm (HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time

---

### 📦 Dependencies Added

- `python-jose[cryptography]`: JWT token handling
- `passlib[bcrypt]`: Password hashing and verification
- `python-multipart`: Form data support

---

### 🧪 Testing

#### Unit Tests (`tests/unit/test_auth.py`)

Comprehensive test coverage for authentication flows:
- ✅ User registration (normal and admin users)
- ✅ Duplicate email prevention
- ✅ Invalid password validation
- ✅ User login with correct credentials
- ✅ Login failure with wrong credentials
- ✅ Protected endpoint access with valid token
- ✅ Protected endpoint denial without token
- ✅ Invalid token handling
- ✅ Admin-only endpoint access control
- ✅ Profile retrieval and updates

#### Integration Tests

All authentication workflows tested end-to-end with database integration.

#### Test Results

**✅ 7/7 test suites passed** (as of November 14, 2025)

| Test Suite | Status |
|------------|--------|
| Python version compatibility | ✅ PASSED |
| Dependencies | ✅ PASSED |
| Unit tests | ✅ PASSED |
| Integration tests | ✅ PASSED |
| Full test coverage | ✅ PASSED |
| Authentication tests | ✅ PASSED |
| Book tests | ✅ PASSED |

---

### 📋 API Documentation

#### Postman Collection

**New Collection**: `postman_collection_task2.json`
- Complete API testing suite with authentication flows
- Pre-configured environment variables
- Automated token extraction and storage
- Test scripts for validation

---

## 🔐 Security Features

### 1. Password Security
- ✅ Bcrypt hashing with automatic salt generation
- ✅ Password strength validation (min 8 chars, letters + digits required)
- ✅ Passwords never stored in plain text or returned in responses

### 2. JWT Token Security
- ✅ HS256 algorithm for token signing
- ✅ Configurable expiration (default: 30 minutes)
- ✅ Token validation on every protected request
- ✅ Proper error handling for expired/invalid tokens

### 3. Role-Based Access Control (RBAC)
- **User role**: Can create books, view all books, update own profile
- **Admin role**: All user permissions + delete any book

### 4. Data Privacy
- ✅ User passwords excluded from all API responses
- ✅ Email uniqueness enforced at database level
- ✅ Proper HTTP status codes for security errors (401, 403)

---

## 🗄️ Database Schema Changes

### New Table: `users`

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    role VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
```

### Updated Table: `books`

```sql
ALTER TABLE books ADD COLUMN created_by INTEGER;
ALTER TABLE books ADD CONSTRAINT fk_books_created_by 
    FOREIGN KEY (created_by) REFERENCES users(id);
```

---

## 🚀 Migration Instructions

### 1. Database Migration (Required before running the app)

```bash
python migrate_task2.py
```

### 2. Environment Variables (Update `.env`)

```env
SECRET_KEY=your-secret-key-min-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Tests

```bash
pytest -v
```

---

## 📊 API Changes Summary

| Endpoint | Method | Auth Required | Role Required | Change |
|----------|--------|---------------|---------------|---------|
| `/register` | POST | No | - | ✨ New |
| `/login` | POST | No | - | ✨ New |
| `/me` | GET | Yes | user/admin | ✨ New |
| `/me` | PUT | Yes | user/admin | ✨ New |
| `/books` | GET | No | - | No change |
| `/books/{id}` | GET | No | - | No change |
| `/books` | POST | **Yes** | user/admin | 🔒 Now protected |
| `/books/{id}` | PUT | No | - | No change |
| `/books/{id}` | DELETE | **Yes** | **admin** | 🔒 Now admin-only |

---

## 🔄 Backward Compatibility

- ✅ Existing books without `created_by` remain accessible
- ✅ `created_by` field is nullable for backward compatibility
- ✅ Public endpoints (GET operations) remain unchanged
- ✅ Existing tests updated to support authentication

---

## ✅ Acceptance Criteria Met

- [x] JWT-based authentication implemented
- [x] User registration with email/password
- [x] User login returning JWT tokens
- [x] Password hashing with bcrypt
- [x] Protected endpoints require valid JWT
- [x] Role-based authorization (user/admin)
- [x] Admin-only delete operation
- [x] Book creation tracks creator
- [x] Comprehensive test coverage
- [x] Database migration script provided
- [x] Postman collection updated
- [x] All tests passing

---

## 📚 Documentation

- ✅ API endpoints fully documented with OpenAPI/Swagger
- ✅ Interactive docs available at `/docs` and `/redoc`
- ✅ Postman collection with example requests
- ✅ Migration script with inline documentation

---

## 🎓 What I Learned (Task 2)

- JWT token generation and validation
- Password hashing best practices with bcrypt
- FastAPI dependency injection for authentication
- Role-based access control implementation
- SQLAlchemy relationships and foreign keys
- Database migrations with backward compatibility
- Secure API design patterns

---

## 🔗 Related

- **Base Branch**: `main`
- **Previous PR**: Task 1 - Basic REST API (`basic-rest-api`)
- **Next Task**: Task 3 (TBD)

---

**Ready for Review** ✅

All requirements completed, tested, and documented. The authentication system is production-ready and follows security best practices.

