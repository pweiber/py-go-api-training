"""Unit tests for schema validators."""
import pytest
from src.schemas.validators import validate_isbn


class TestValidateISBN:
    """Test cases for ISBN validator."""

    def test_valid_isbn13_with_dashes(self):
        """Test ISBN-13 with dashes is normalized."""
        assert validate_isbn("978-0-12-345678-9") == "9780123456789"

    def test_valid_isbn13_without_dashes(self):
        """Test ISBN-13 without dashes remains unchanged."""
        assert validate_isbn("9780123456789") == "9780123456789"

    def test_valid_isbn10_with_dashes(self):
        """Test ISBN-10 with dashes is normalized."""
        assert validate_isbn("0-306-40615-2") == "0306406152"

    def test_valid_isbn10_with_x_checkdigit(self):
        """Test ISBN-10 with X check digit."""
        assert validate_isbn("0-306-40615-X") == "030640615X"
        assert validate_isbn("0-306-40615-x") == "030640615X"  # Lowercase X

    def test_isbn_with_spaces(self):
        """Test ISBN with spaces is normalized."""
        assert validate_isbn("978 0 12 345678 9") == "9780123456789"

    def test_none_returns_none(self):
        """Test None input returns None."""
        assert validate_isbn(None) is None

    def test_invalid_length(self):
        """Test ISBN with invalid length raises error."""
        with pytest.raises(ValueError, match="must be 10 or 13 characters"):
            validate_isbn("123456789")

    def test_invalid_characters(self):
        """Test ISBN with letters raises error."""
        with pytest.raises(ValueError, match="must contain only digits"):
            validate_isbn("978ABC3456789")

    def test_isbn13_with_x_raises_error(self):
        """Test ISBN-13 cannot have X check digit."""
        with pytest.raises(ValueError, match="must contain only digits"):
            validate_isbn("978012345678X")
