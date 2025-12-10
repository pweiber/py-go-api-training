"""
Main FastAPI application entry point.

This module initializes the FastAPI application, registers middleware,
exception handlers, and routes.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError, DataError, SQLAlchemyError, OperationalError

from src.core.config import settings
from src.core.database import init_db
from src.core.exceptions import (
    integrity_error_handler,
    data_error_handler,
    operational_error_handler,
    sqlalchemy_error_handler,
    database_exception_handler,
    DatabaseException,
)
from src.api.v1.endpoints import books, auth, users


app = FastAPI(
    title="Intern Training API",
    description="Production-ready FastAPI application for intern training program",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ============================================================================
# EXCEPTION HANDLERS REGISTRATION
# ============================================================================
# Register in order of specificity (most specific first, most general last)

# Most specific: Handle integrity errors (unique constraints, foreign keys, etc.)
app.add_exception_handler(IntegrityError, integrity_error_handler)

# Handle data errors (invalid types, values too long, etc.)
app.add_exception_handler(DataError, data_error_handler)

# Handle operational errors (connection issues, timeouts, etc.)
app.add_exception_handler(OperationalError, operational_error_handler)

# Handle our custom database exceptions
app.add_exception_handler(DatabaseException, database_exception_handler)

# Most general: Catch-all for any other SQLAlchemy errors
app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)

# ============================================================================
# MIDDLEWARE CONFIGURATION
# ============================================================================

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# HEALTH CHECK AND ROOT ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.

    Returns:
        dict: Service health status
    """
    return {
        "status": "healthy",
        "service": "intern-training-api",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """
    Root endpoint with API information.

    Returns:
        dict: API welcome message and documentation links
    """
    return {
        "message": "Book Store API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# ============================================================================
# ROUTER REGISTRATION
# ============================================================================

# Include API routers
app.include_router(books.router, prefix="/api/v1", tags=["books"])
app.include_router(auth.router, tags=["auth"])
app.include_router(users.router, tags=["users"])

# ============================================================================
# APPLICATION STARTUP
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    # Initialize database tables when running directly
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
