"""
Additional tests for exception handling to increase coverage.
Tests the exception classes, handlers, and utility functions.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from fastapi import Request, status
from sqlalchemy.exc import IntegrityError, DataError, OperationalError, SQLAlchemyError

from src.core.exceptions import (
    DatabaseException,
    DuplicateResourceException,
    ResourceNotFoundException,
    ForeignKeyViolationException,
    InvalidDataException,
    integrity_error_handler,
    data_error_handler,
    operational_error_handler,
    sqlalchemy_error_handler,
    database_exception_handler,
    parse_integrity_error,
)


class TestCustomExceptionClasses:
    """Test custom exception class initialization and properties."""

    def test_database_exception_default_status_code(self):
        """Test DatabaseException with default status code."""
        exc = DatabaseException("Test error message")
        assert exc.message == "Test error message"
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_database_exception_custom_status_code(self):
        """Test DatabaseException with custom status code."""
        exc = DatabaseException("Test error", status_code=status.HTTP_400_BAD_REQUEST)
        assert exc.message == "Test error"
        assert exc.status_code == status.HTTP_400_BAD_REQUEST

    def test_duplicate_resource_exception(self):
        """Test DuplicateResourceException initialization."""
        exc = DuplicateResourceException("Book", "ISBN 1234567890")
        assert "Book" in exc.message
        assert "ISBN 1234567890" in exc.message
        assert "already exists" in exc.message
        assert exc.status_code == status.HTTP_409_CONFLICT

    def test_resource_not_found_exception(self):
        """Test ResourceNotFoundException initialization."""
        exc = ResourceNotFoundException("Author", "id 42")
        assert "Author" in exc.message
        assert "id 42" in exc.message
        assert "not found" in exc.message
        assert exc.status_code == status.HTTP_404_NOT_FOUND

    def test_foreign_key_violation_exception_default_message(self):
        """Test ForeignKeyViolationException with default message."""
        exc = ForeignKeyViolationException()
        assert "relationship constraint" in exc.message.lower()
        assert exc.status_code == status.HTTP_400_BAD_REQUEST

    def test_foreign_key_violation_exception_custom_message(self):
        """Test ForeignKeyViolationException with custom message."""
        exc = ForeignKeyViolationException("Cannot delete: referenced by reviews")
        assert exc.message == "Cannot delete: referenced by reviews"
        assert exc.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_data_exception_default_message(self):
        """Test InvalidDataException with default message."""
        exc = InvalidDataException()
        assert "invalid data" in exc.message.lower()
        assert exc.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_data_exception_custom_message(self):
        """Test InvalidDataException with custom message."""
        exc = InvalidDataException("ISBN format is invalid")
        assert exc.message == "ISBN format is invalid"
        assert exc.status_code == status.HTTP_400_BAD_REQUEST


class TestParseIntegrityError:
    """Test the parse_integrity_error utility function."""

    def test_parse_duplicate_isbn_error(self):
        """Test parsing duplicate ISBN error."""
        mock_exc = Mock(spec=IntegrityError)
        mock_exc.orig = Mock()
        mock_exc.orig.__str__ = Mock(return_value="unique constraint violated on column isbn")

        result = parse_integrity_error(mock_exc)

        assert result["type"] == "duplicate_isbn"
        assert "ISBN" in result["message"]
        assert result["status_code"] == status.HTTP_409_CONFLICT

    def test_parse_duplicate_email_error(self):
        """Test parsing duplicate email error."""
        mock_exc = Mock(spec=IntegrityError)
        mock_exc.orig = Mock()
        mock_exc.orig.__str__ = Mock(return_value="duplicate key value violates unique constraint on email")

        result = parse_integrity_error(mock_exc)

        assert result["type"] == "duplicate_email"
        assert "email" in result["message"].lower()
        assert result["status_code"] == status.HTTP_409_CONFLICT

    def test_parse_generic_duplicate_error(self):
        """Test parsing generic duplicate error."""
        mock_exc = Mock(spec=IntegrityError)
        mock_exc.orig = Mock()
        mock_exc.orig.__str__ = Mock(return_value="unique constraint violated")

        result = parse_integrity_error(mock_exc)

        assert result["type"] == "duplicate_resource"
        assert result["status_code"] == status.HTTP_409_CONFLICT

    def test_parse_foreign_key_referenced_error(self):
        """Test parsing foreign key error when resource is referenced."""
        mock_exc = Mock(spec=IntegrityError)
        mock_exc.orig = Mock()
        mock_exc.orig.__str__ = Mock(return_value="violates foreign key constraint: still referenced from table reviews")

        result = parse_integrity_error(mock_exc)

        assert result["type"] == "foreign_key_referenced"
        assert "cannot delete" in result["message"].lower()
        assert result["status_code"] == status.HTTP_409_CONFLICT

    def test_parse_foreign_key_violation_error(self):
        """Test parsing foreign key violation (resource doesn't exist)."""
        mock_exc = Mock(spec=IntegrityError)
        mock_exc.orig = Mock()
        mock_exc.orig.__str__ = Mock(return_value="violates foreign key constraint")

        result = parse_integrity_error(mock_exc)

        assert result["type"] == "foreign_key_violation"
        assert "not exist" in result["message"].lower()
        assert result["status_code"] == status.HTTP_400_BAD_REQUEST

    def test_parse_not_null_constraint_with_column_name(self):
        """Test parsing NOT NULL constraint with column name."""
        mock_exc = Mock(spec=IntegrityError)
        mock_exc.orig = Mock()
        mock_exc.orig.__str__ = Mock(return_value='null value in column "title" violates not-null constraint')

        result = parse_integrity_error(mock_exc)

        assert result["type"] == "missing_required_field"
        assert "title" in result["message"]
        assert result["status_code"] == status.HTTP_400_BAD_REQUEST

    def test_parse_not_null_constraint_without_column_name(self):
        """Test parsing NOT NULL constraint without column name."""
        mock_exc = Mock(spec=IntegrityError)
        mock_exc.orig = Mock()
        mock_exc.orig.__str__ = Mock(return_value="not null constraint violated")

        result = parse_integrity_error(mock_exc)

        assert result["type"] == "missing_required_field"
        assert result["status_code"] == status.HTTP_400_BAD_REQUEST

    def test_parse_check_constraint_error(self):
        """Test parsing CHECK constraint error."""
        mock_exc = Mock(spec=IntegrityError)
        mock_exc.orig = Mock()
        mock_exc.orig.__str__ = Mock(return_value="check constraint violated")

        result = parse_integrity_error(mock_exc)

        assert result["type"] == "check_constraint_violation"
        assert result["status_code"] == status.HTTP_400_BAD_REQUEST

    def test_parse_generic_integrity_error(self):
        """Test parsing generic integrity error."""
        mock_exc = Mock(spec=IntegrityError)
        mock_exc.orig = Mock()
        mock_exc.orig.__str__ = Mock(return_value="some unknown database error")

        result = parse_integrity_error(mock_exc)

        assert result["type"] == "integrity_error"
        assert result["status_code"] == status.HTTP_400_BAD_REQUEST

    def test_parse_integrity_error_no_orig(self):
        """Test parsing when exc.orig is None."""
        mock_exc = Mock(spec=IntegrityError)
        mock_exc.orig = None
        mock_exc.__str__ = Mock(return_value="database error")

        result = parse_integrity_error(mock_exc)

        assert "original_message" in result


class TestExceptionHandlers:
    """Test async exception handler functions."""

    def _create_mock_request(self, method="POST", path="/api/v1/books"):
        """Helper to create a mock request."""
        mock_request = Mock(spec=Request)
        mock_request.method = method
        mock_request.url = Mock()
        mock_request.url.path = path
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"
        return mock_request

    @pytest.mark.asyncio
    async def test_integrity_error_handler(self):
        """Test integrity error handler."""
        mock_request = self._create_mock_request()
        mock_exc = Mock(spec=IntegrityError)
        mock_exc.orig = Mock()
        mock_exc.orig.__str__ = Mock(return_value="unique constraint on isbn")

        response = await integrity_error_handler(mock_request, mock_exc)

        assert response.status_code == status.HTTP_409_CONFLICT
        assert "error_type" in response.body.decode()

    @pytest.mark.asyncio
    async def test_integrity_error_handler_no_client(self):
        """Test integrity error handler when request has no client."""
        mock_request = self._create_mock_request()
        mock_request.client = None
        mock_exc = Mock(spec=IntegrityError)
        mock_exc.orig = Mock()
        mock_exc.orig.__str__ = Mock(return_value="unique constraint")

        response = await integrity_error_handler(mock_request, mock_exc)

        assert response.status_code == status.HTTP_409_CONFLICT

    @pytest.mark.asyncio
    async def test_data_error_handler(self):
        """Test data error handler."""
        mock_request = self._create_mock_request()
        mock_exc = Mock(spec=DataError)
        mock_exc.orig = Mock()
        mock_exc.orig.__str__ = Mock(return_value="invalid data format")

        response = await data_error_handler(mock_request, mock_exc)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert b"data_error" in response.body

    @pytest.mark.asyncio
    async def test_data_error_handler_value_too_long(self):
        """Test data error handler with value too long error."""
        mock_request = self._create_mock_request()
        mock_exc = Mock(spec=DataError)
        mock_exc.orig = Mock()
        mock_exc.orig.__str__ = Mock(return_value="value too long for column")

        response = await data_error_handler(mock_request, mock_exc)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        body = response.body.decode()
        assert "exceed maximum length" in body

    @pytest.mark.asyncio
    async def test_data_error_handler_invalid_input_syntax(self):
        """Test data error handler with invalid input syntax."""
        mock_request = self._create_mock_request()
        mock_exc = Mock(spec=DataError)
        mock_exc.orig = Mock()
        mock_exc.orig.__str__ = Mock(return_value="invalid input syntax for type")

        response = await data_error_handler(mock_request, mock_exc)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_data_error_handler_numeric_out_of_range(self):
        """Test data error handler with numeric overflow."""
        mock_request = self._create_mock_request()
        mock_exc = Mock(spec=DataError)
        mock_exc.orig = Mock()
        mock_exc.orig.__str__ = Mock(return_value="numeric field out of range")

        response = await data_error_handler(mock_request, mock_exc)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_data_error_handler_no_orig(self):
        """Test data error handler when exc.orig is None."""
        mock_request = self._create_mock_request()
        mock_exc = Mock(spec=DataError)
        mock_exc.orig = None
        mock_exc.__str__ = Mock(return_value="data error")

        response = await data_error_handler(mock_request, mock_exc)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_operational_error_handler(self):
        """Test operational error handler."""
        mock_request = self._create_mock_request()
        mock_exc = Mock(spec=OperationalError)
        mock_exc.orig = Mock()
        mock_exc.orig.__str__ = Mock(return_value="connection refused")

        response = await operational_error_handler(mock_request, mock_exc)

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert b"operational_error" in response.body

    @pytest.mark.asyncio
    async def test_operational_error_handler_no_orig(self):
        """Test operational error handler when exc.orig is None."""
        mock_request = self._create_mock_request()
        mock_exc = Mock(spec=OperationalError)
        mock_exc.orig = None
        mock_exc.__str__ = Mock(return_value="database connection lost")

        response = await operational_error_handler(mock_request, mock_exc)

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    @pytest.mark.asyncio
    async def test_sqlalchemy_error_handler(self):
        """Test generic SQLAlchemy error handler."""
        mock_request = self._create_mock_request()
        mock_exc = Mock(spec=SQLAlchemyError)
        mock_exc.__str__ = Mock(return_value="unexpected database error")

        response = await sqlalchemy_error_handler(mock_request, mock_exc)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert b"database_error" in response.body

    @pytest.mark.asyncio
    async def test_database_exception_handler(self):
        """Test custom database exception handler."""
        mock_request = self._create_mock_request()
        exc = DuplicateResourceException("Book", "ISBN 123")

        response = await database_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_409_CONFLICT
        body = response.body.decode()
        assert "Book" in body
        assert "ISBN 123" in body

    @pytest.mark.asyncio
    async def test_database_exception_handler_not_found(self):
        """Test database exception handler with not found exception."""
        mock_request = self._create_mock_request(method="GET", path="/api/v1/books/999")
        exc = ResourceNotFoundException("Book", "id 999")

        response = await database_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_exception_handler_no_client_info(self):
        """Test exception handlers when client info is None."""
        mock_request = self._create_mock_request()
        mock_request.client = None

        exc = DatabaseException("Test error")
        response = await database_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

