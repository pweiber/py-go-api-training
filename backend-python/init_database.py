#!/usr/bin/env python3
"""
Database initialization and verification script.
Run this to set up the database tables and verify connection.
"""
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.database import engine, init_db, Base
from src.models import Book, User
from sqlalchemy import text

def check_database_connection():
    """Check if database connection is working."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def initialize_database():
    """Initialize database tables."""
    try:
        print("Creating database tables...")
        init_db()
        print("✅ Database tables created successfully!")
        
        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public'"
            ))
            tables = [row[0] for row in result]
            print(f"📊 Tables created: {tables}")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main execution."""
    print("=" * 80)
    print("DATABASE INITIALIZATION SCRIPT")
    print("=" * 80)
    print()
    
    # Step 1: Check connection
    print("Step 1: Checking database connection...")
    if not check_database_connection():
        print("\n⚠️  Please ensure:")
        print("   1. PostgreSQL is running")
        print("   2. Database 'bookstore' exists")
        print("   3. User 'postgres' has correct password")
        print("   4. .env file has correct DATABASE_URL")
        sys.exit(1)
    
    print()
    
    # Step 2: Initialize tables
    print("Step 2: Initializing database tables...")
    if not initialize_database():
        print("\n⚠️  Database initialization failed!")
        sys.exit(1)
    
    print()
    print("=" * 80)
    print("✅ DATABASE READY!")
    print("=" * 80)
    print()
    print("You can now start the API with:")
    print("  uvicorn src.main:app --reload")
    print()

if __name__ == "__main__":
    main()

