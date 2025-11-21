"""Reusable Pydantic validators for schema validation."""


def validate_isbn(v: str | None) -> str | None:
    """
    Normalize and validate ISBN-10 or ISBN-13.

    Removes dashes and spaces, validates format, and returns normalized ISBN.

    Args:
        v: ISBN string with optional dashes/spaces, or None

    Returns:
        Normalized ISBN (digits only, uppercase X for ISBN-10 check digit)
        Returns None if input is None

    Raises:
        ValueError: If ISBN format is invalid

    Examples:
        >>> validate_isbn("978-0-12-345678-9")
        '9780123456789'
        >>> validate_isbn("0-306-40615-2")
        '0306406152'
        >>> validate_isbn("0-306-40615-X")
        '030640615X'
    """
    if v is None:
        return v

    # Remove dashes, spaces, and convert to uppercase
    cleaned = v.replace('-', '').replace(' ', '').upper()

    # Validate length (ISBN-10 or ISBN-13)
    if len(cleaned) not in [10, 13]:
        raise ValueError(
            f'ISBN must be 10 or 13 characters after removing dashes/spaces. '
            f'Got {len(cleaned)} characters.'
        )

    # Validate that it contains only digits (allowing 'X' for ISBN-10 check digit)
    if not (cleaned[:-1].isdigit() and
            (cleaned[-1].isdigit() or (len(cleaned) == 10 and cleaned[-1] == 'X'))):
        raise ValueError('ISBN must contain only digits (ISBN-10 may end with X)')

    return cleaned
