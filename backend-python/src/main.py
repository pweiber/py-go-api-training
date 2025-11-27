"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.database import init_db
from src.api.v1.endpoints import books, auth, users


app = FastAPI(
    title="Intern Training API",
    description="Production-ready FastAPI application for intern training program",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup."""
    init_db()

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "service": "intern-training-api"}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {"message": "Book Store API"}

# Include routers
app.include_router(auth.router, tags=["authentication"])
app.include_router(books.router, tags=["books"])
app.include_router(users.router, tags=["users"])

if __name__ == "__main__":
    import uvicorn
    # Initialize database tables when running directly
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
