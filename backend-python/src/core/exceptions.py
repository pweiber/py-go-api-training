"""
Exception handling for the application.

This module contains:
- Custom exception classes (Section 1)
- Exception handler functions for FastAPI (Section 2)  
- Helper utilities for error parsing (Section 3)

As the project grows, this can be split into:
- exceptions.py (classes only)
- exception_handlers.py (handlers only)
"""
import logging
from typing import Dict, Any
from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, DataError, SQLAlchemyError, OperationalError

# Configure logger
logger = logging.getLogger(__name__)


# ============================================================================
# SECTION 1: CUSTOM EXCEPTION CLASSES
# ============================================================================

class DatabaseException(Exception):
    """
    Base exception for database-related errors.
    
    Attributes:
        message: Human-readable error message
        status_code: HTTP status code to return
    """
    
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DuplicateResourceException(DatabaseException):
    """Exception raised when attempting to create a duplicate resource."""
    
    def __init__(self, resource_type: str, identifier: str):
        message = f"{resource_type} with {identifier} already exists"
        super().__init__(message, status_code=status.HTTP_409_CONFLICT)


class ResourceNotFoundException(DatabaseException):
    """Exception raised when a requested resource is not found."""
    
    def __init__(self, resource_type: str, identifier: str):
        message = f"{resource_type} with {identifier} not found"
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND)


class ForeignKeyViolationException(DatabaseException):
    """Exception raised when a foreign key constraint is violated."""
    
    def __init__(self, message: str = "Operation violates a relationship constraint"):
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST)


class InvalidDataException(DatabaseException):
    """Exception raised when data validation fails at database level."""
    
    def __init__(self, message: str = "Invalid data format or value"):
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# SECTION 2: FASTAPI EXCEPTION HANDLERS
# ============================================================================

async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """
    Handle SQLAlchemy IntegrityError exceptions.
    
    This catches database integrity violations (unique constraints, foreign keys, 
    NOT NULL constraints, etc.) and returns appropriate HTTP responses with 
    sanitized error messages.
    
    Args:
        request: The incoming FastAPI request
        exc: The IntegrityError exception raised by SQLAlchemy
        
    Returns:
        JSONResponse with appropriate status code and user-friendly error message
    """
    error_info = parse_integrity_error(exc)
    
    # Log the full error for debugging (with stack trace)
    logger.error(
        f"Database integrity error on {request.method} {request.url.path}: "
        f"{error_info['original_message']}",
        exc_info=True,
        extra={
            "method": request.method,
            "path": request.url.path,
            "error_type": error_info["type"],
            "client_ip": request.client.host if request.client else None,
        }
    )
    
    return JSONResponse(
        status_code=error_info["status_code"],
        content={
            "detail": error_info["message"],
            "error_type": error_info["type"],
        }
    )


async def data_error_handler(request: Request, exc: DataError) -> JSONResponse:
    """
    Handle SQLAlchemy DataError exceptions.
    
    This catches data-related errors like invalid data types, values that are 
    too long for the column, numeric overflow, etc.
    
    Args:
        request: The incoming FastAPI request
        exc: The DataError exception raised by SQLAlchemy
        
    Returns:
        JSONResponse with 400 status and sanitized error message
    """
    error_message = str(exc.orig) if exc.orig else str(exc)
    
    logger.error(
        f"Database data error on {request.method} {request.url.path}: {error_message}",
        exc_info=True,
        extra={
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else None,
        }
    )
    
    # Parse specific data errors
    user_message = "Invalid data format or value"
    if "value too long" in error_message.lower():
        user_message = "One or more field values exceed maximum length"
    elif "invalid input syntax" in error_message.lower():
        user_message = "Invalid data format for one or more fields"
    elif "numeric" in error_message.lower() and "out of range" in error_message.lower():
        user_message = "Numeric value is out of acceptable range"
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": user_message,
            "error_type": "data_error",
        }
    )


async def operational_error_handler(request: Request, exc: OperationalError) -> JSONResponse:
    """
    Handle SQLAlchemy OperationalError exceptions.
    
    This catches operational database errors like connection failures, 
    transaction errors, etc.
    
    Args:
        request: The incoming FastAPI request
        exc: The OperationalError exception raised by SQLAlchemy
        
    Returns:
        JSONResponse with 503 status indicating service unavailability
    """
    error_message = str(exc.orig) if exc.orig else str(exc)
    
    logger.critical(
        f"Database operational error on {request.method} {request.url.path}: {error_message}",
        exc_info=True,
        extra={
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else None,
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": "Database service temporarily unavailable. Please try again later.",
            "error_type": "operational_error",
        }
    )


async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Handle generic SQLAlchemy exceptions.
    
    This is a catch-all for database errors not handled by more specific handlers.
    Should be registered last so more specific handlers take precedence.
    
    Args:
        request: The incoming FastAPI request
        exc: The SQLAlchemyError exception
        
    Returns:
        JSONResponse with 500 status and generic error message
    """
    logger.error(
        f"Unexpected database error on {request.method} {request.url.path}: {str(exc)}",
        exc_info=True,
        extra={
            "method": request.method,
            "path": request.url.path,
            "error_type": type(exc).__name__,
            "client_ip": request.client.host if request.client else None,
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected database error occurred. Please try again or contact support.",
            "error_type": "database_error",
        }
    )


async def database_exception_handler(request: Request, exc: DatabaseException) -> JSONResponse:
    """
    Handle custom DatabaseException exceptions.
    
    This handles our custom exception classes (DuplicateResourceException, 
    ResourceNotFoundException, etc.)
    
    Args:
        request: The incoming FastAPI request
        exc: The custom DatabaseException
        
    Returns:
        JSONResponse with appropriate status code and error message
    """
    logger.error(
        f"Database exception on {request.method} {request.url.path}: {exc.message}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": exc.status_code,
            "client_ip": request.client.host if request.client else None,
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "error_type": type(exc).__name__.replace("Exception", "").lower(),
        }
    )


# ============================================================================
# SECTION 3: HELPER UTILITIES
# ============================================================================

def parse_integrity_error(exc: IntegrityError) -> Dict[str, Any]:
    """
    Parse IntegrityError to extract meaningful information.
    
    Args:
        exc: The IntegrityError exception
        
    Returns:
        Dictionary containing parsed error information:
        - type: Error type classification
        - message: User-friendly error message
        - status_code: Appropriate HTTP status code
        - original_message: Original database error message
    """
    error_message = str(exc.orig) if exc.orig else str(exc)
    error_message_lower = error_message.lower()
    
    # Store original message for logging
    original_message = error_message
    
    # Unique constraint violation
    if "unique constraint" in error_message_lower or "duplicate key" in error_message_lower:
        # Try to extract which field caused the violation
        if "isbn" in error_message_lower:
            return {
                "type": "duplicate_isbn",
                "message": "A book with this ISBN already exists",
                "status_code": status.HTTP_409_CONFLICT,
                "original_message": original_message,
            }
        elif "email" in error_message_lower:
            return {
                "type": "duplicate_email",
                "message": "This email is already registered",
                "status_code": status.HTTP_409_CONFLICT,
                "original_message": original_message,
            }
        else:
            return {
                "type": "duplicate_resource",
                "message": "This resource already exists in the database",
                "status_code": status.HTTP_409_CONFLICT,
                "original_message": original_message,
            }
    
    # Foreign key constraint violation
    elif "foreign key constraint" in error_message_lower or "violates foreign key" in error_message_lower:
        # Check if it's a deletion issue
        if "still referenced" in error_message_lower or "on delete" in error_message_lower:
            return {
                "type": "foreign_key_referenced",
                "message": "Cannot delete this resource because it is referenced by other records",
                "status_code": status.HTTP_409_CONFLICT,
                "original_message": original_message,
            }
        else:
            return {
                "type": "foreign_key_violation",
                "message": "Referenced resource does not exist",
                "status_code": status.HTTP_400_BAD_REQUEST,
                "original_message": original_message,
            }
    
    # NOT NULL constraint violation
    elif "not null constraint" in error_message_lower or "null value" in error_message_lower:
        # Try to extract field name
        field_match = None
        if "column" in error_message_lower:
            # PostgreSQL format: 'null value in column "field_name" violates not-null constraint'
            import re
            match = re.search(r'column "([^"]+)"', error_message)
            if match:
                field_match = match.group(1)
        
        message = f"Required field '{field_match}' is missing" if field_match else "Required field is missing"
        return {
            "type": "missing_required_field",
            "message": message,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "original_message": original_message,
        }
    
    # Check constraint violation
    elif "check constraint" in error_message_lower:
        return {
            "type": "check_constraint_violation",
            "message": "Data validation failed: value does not meet required criteria",
            "status_code": status.HTTP_400_BAD_REQUEST,
            "original_message": original_message,
        }
    
    # Generic integrity error
    return {
        "type": "integrity_error",
        "message": "Database integrity constraint violated",
        "status_code": status.HTTP_400_BAD_REQUEST,
        "original_message": original_message,
    }


def get_error_context(request: Request) -> Dict[str, Any]:
    """
    Extract useful context from request for error logging.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        Dictionary with request context information
    """
    return {
        "method": request.method,
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "client_host": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }

