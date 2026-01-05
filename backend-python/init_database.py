#!/usr/bin/env python3
"""
Database initialization and verification script.
Run this to verify database connection and seed initial data.
"""
import sys
import os
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.database import engine, SessionLocal
from src.models import User
from src.models.user import UserRole
from src.core.auth import hash_password
from sqlalchemy import text

def check_database_connection():
    """Check if database connection is working."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            value = result.scalar()
            if value == 1:
                print("✅ Database connection successful!")
                return True
            else:
                print(f"❌ Unexpected result from database: {value}")
                return False
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def verify_migrations():
    """Verify that migrations have been applied."""
    try:
        with engine.connect() as conn:
            # Check if alembic_version table exists
            result = conn.execute(text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = 'alembic_version')"
            ))
            if not result.scalar():
                print("❌ No migrations applied. Run 'alembic upgrade head' first.")
                return False

            # Get current migration version
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()
            print(f"✅ Current migration version: {version}")

            # List all tables
            result = conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' ORDER BY table_name"
            ))
            tables = [row[0] for row in result]
            print(f"📊 Tables found: {tables}")
            return True
    except Exception as e:
        print(f"❌ Migration verification failed: {e}")
        return False

def seed_initial_admin():
    """
    Seed the initial admin user if no users exist.

    Reads admin credentials from environment variables:
    - INITIAL_ADMIN_EMAIL (default: admin@example.com)
    - INITIAL_ADMIN_PASSWORD (default: Admin123456!)
    """
    db = SessionLocal()
    try:
        # Check if any users exist
        user_count = db.query(User).count()

        if user_count > 0:
            print("ℹ️  Users already exist, skipping admin seeding.")
            return True

        # Get admin credentials from environment
        admin_email = os.getenv("INITIAL_ADMIN_EMAIL", "admin@example.com")
        admin_password = os.getenv("INITIAL_ADMIN_PASSWORD", "Admin123456!")

        print(f"Creating initial admin user: {admin_email}")

        # Create admin user
        admin_user = User(
            email=admin_email,
            hashed_password=hash_password(admin_password),
            role=UserRole.ADMIN,
            is_active=True
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print(f"✅ Initial admin user created successfully!")
        print(f"   Email: {admin_email}")
        print(f"   Password: [set from INITIAL_ADMIN_PASSWORD or default]")
        print(f"   ⚠️  Remember to change the password after first login!")

        return True

    except Exception as e:
        print(f"❌ Admin seeding failed: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

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
        print("   3. .env file has correct DATABASE_URL")
        sys.exit(1)

    print()

    # Step 2: Verify migrations
    print("Step 2: Verifying migrations...")
    if not verify_migrations():
        print("\n⚠️  Run migrations first:")
        print("   alembic upgrade head")
        sys.exit(1)

    print()

    # Step 3: Seed initial admin user
    print("Step 3: Seeding initial admin user...")
    if not seed_initial_admin():
        print("\n⚠️  Admin seeding failed!")
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
