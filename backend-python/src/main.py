"""
Main FastAPI application entry point.

"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# TODO: Import routers from api.v1.endpoints as you create them
# from src.api.v1.endpoints import books, auth, users

app = FastAPI(
    title="Intern Training API",
    description="Production-ready FastAPI application for intern training program",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware configuration
# TODO: Update allowed origins based on your frontend URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "service": "intern-training-api"}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to the Intern Training API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# TODO: Include routers as you create them
# app.include_router(books.router, prefix="/api/v1", tags=["books"])
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
# app.include_router(users.router, prefix="/api/v1/users", tags=["users"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
