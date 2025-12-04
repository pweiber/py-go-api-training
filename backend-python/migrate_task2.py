"""
Database migration script to add users table and update books table.
This script should be run after Task 1 to add authentication support.
"""
from sqlalchemy import create_engine, text
from src.core.config import settings

def run_migration():
    """Run database migration for Task 2 (Authentication)."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.begin() as connection:
        print("Starting Task 2 migration...")
        
        # Create users table
        print("Creating users table...")
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE NOT NULL,
                role VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
            );
        """))
        
        # Create index on email
        print("Creating index on users.email...")
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        """))

        # Add created_by column to books table (if it doesn't exist)
        print("Adding created_by column to books table...")
        connection.execute(text("""
            DO $$
            BEGIN
                -- Add created_by column if it does not exist
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='books' AND column_name='created_by'
                ) THEN
                    ALTER TABLE books ADD COLUMN created_by INTEGER;
                END IF;

                -- Add foreign key constraint if it does not exist
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints
                    WHERE table_name='books' AND constraint_name='fk_books_created_by'
                ) THEN
                    ALTER TABLE books ADD CONSTRAINT fk_books_created_by
                        FOREIGN KEY (created_by) REFERENCES users(id);
                END IF;
            END $$;
        """))

        print("Migration completed successfully!")
        print("\nNew tables and columns:")
        print("  - users (id, email, hashed_password, is_active, role, created_at)")
        print("  - books.created_by (foreign key to users.id)")

if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"Migration failed: {e}")
        raise

