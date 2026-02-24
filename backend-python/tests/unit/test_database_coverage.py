"""
Additional tests for database module to increase coverage.
Tests the get_db dependency and init_db function.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from src.core.database import get_db, init_db, Base


class TestGetDbDependency:
    """Test the get_db dependency function."""

    def test_get_db_yields_session(self):
        """Test that get_db yields a database session."""
        # The actual get_db is already tested through the API tests
        # This test ensures the generator works correctly
        gen = get_db()
        try:
            db = next(gen)
            assert db is not None
        except StopIteration:
            pass
        finally:
            try:
                gen.close()
            except Exception:
                pass

    def test_get_db_rollback_on_exception(self):
        """Test that get_db rolls back on exception."""
        from src.core.database import SessionLocal

        # Create a mock session
        mock_session = MagicMock(spec=Session)

        with patch('src.core.database.SessionLocal', return_value=mock_session):
            gen = get_db()
            try:
                next(gen)
                # Simulate an exception being thrown
                gen.throw(ValueError("Test exception"))
            except ValueError:
                pass

            # Verify rollback was called
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()

    def test_get_db_closes_session_finally(self):
        """Test that get_db closes session in finally block."""
        from src.core.database import SessionLocal

        mock_session = MagicMock(spec=Session)

        with patch('src.core.database.SessionLocal', return_value=mock_session):
            gen = get_db()
            next(gen)

            # Complete the generator normally
            try:
                next(gen)
            except StopIteration:
                pass

            mock_session.close.assert_called_once()


class TestInitDb:
    """Test the init_db function."""

    def test_init_db_creates_tables(self):
        """Test that init_db creates all tables."""
        with patch.object(Base.metadata, 'create_all') as mock_create:
            init_db()
            mock_create.assert_called_once()

    def test_init_db_imports_models(self):
        """Test that init_db imports all necessary models."""
        # This ensures that the models are registered with SQLAlchemy
        # The actual table creation is tested via integration tests

        # Simply calling init_db should not raise any import errors
        try:
            init_db()
        except ImportError as e:
            pytest.fail(f"init_db failed to import models: {e}")

