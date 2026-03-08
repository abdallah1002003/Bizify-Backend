"""Custom exception classes for structured error handling.

This module defines project-specific exceptions for different error scenarios,
providing clear error messages and context for debugging and client responses.
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class AppException(Exception):
    """Base exception class for all application exceptions.
    
    Provides a consistent structure for error messages and context information.
    
    Attributes:
        message: Human-readable error message
        code: Error code for logging and tracking
        details: Additional context information
    """
    
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ) -> None:
        """Initialize AppException.
        
        Args:
            message: Clear description of the error
            code: Machine-readable error code
            details: Additional context (optional)
            status_code: HTTP status code (default: 500)
        """
        self.message = message
        self.code = code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(AppException):
    """Raised when input validation fails.
    
    Used for invalid request payloads, missing required fields, or
    incorrect data types.
    """
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize ValidationError.
        
        Args:
            message: Description of what validation failed
            field: Name of the field that failed validation (optional)
            details: Additional validation context
        """
        error_details = details or {}
        if field:
            error_details["field"] = field
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details=error_details,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class ResourceNotFoundError(AppException):
    """Raised when a requested resource does not exist.
    
    Typical use: trying to fetch a user, subscription, or payment that
    doesn't exist in the database.
    """
    
    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize ResourceNotFoundError.
        
        Args:
            resource_type: Type of resource (e.g., 'User', 'Subscription')
            resource_id: Identifier of the missing resource
            details: Additional context
        """
        message = f"{resource_type} with ID '{resource_id}' not found"
        error_details = details or {}
        error_details.update({
            "resource_type": resource_type,
            "resource_id": resource_id
        })
        super().__init__(
            message=message,
            code="NOT_FOUND",
            details=error_details,
            status_code=status.HTTP_404_NOT_FOUND
        )


class AuthenticationError(AppException):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            details=details,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class BadRequestError(AppException):
    """Raised when the request is malformed or invalid."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            message=message,
            code="BAD_REQUEST",
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST
        )



class AccessDeniedError(AppException):
    """Raised when user lacks required permissions.
    
    Used for authorization failures (user trying to access another
    user's data, insufficient role permissions, etc).
    """
    
    def __init__(
        self,
        action: str,
        resource_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize AccessDeniedError.
        
        Args:
            action: Action being denied (e.g., 'update', 'delete')
            resource_type: Type of resource (optional)
            details: Additional context
        """
        resource_part = f" {resource_type}" if resource_type else ""
        message = f"Access denied: cannot {action}{resource_part}"
        error_details = details or {}
        error_details.update({
            "action": action,
            "resource_type": resource_type
        })
        super().__init__(
            message=message,
            code="ACCESS_DENIED",
            details=error_details,
            status_code=status.HTTP_403_FORBIDDEN
        )


class ConflictError(AppException):
    """Raised when operation conflicts with existing data.
    
    Use cases:
    - Email already registered
    - Duplicate subscription for user
    - Stripe operation conflicts
    """
    
    def __init__(
        self,
        message: str,
        conflict_field: Optional[str] = None,
        existing_value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize ConflictError.
        
        Args:
            message: Description of the conflict
            conflict_field: Field causing the conflict (optional)
            existing_value: Current value of the conflicting field
            details: Additional context
        """
        error_details = details or {}
        if conflict_field:
            error_details["conflict_field"] = conflict_field
        if existing_value:
            error_details["existing_value"] = str(existing_value)
        super().__init__(
            message=message,
            code="CONFLICT",
            details=error_details,
            status_code=status.HTTP_409_CONFLICT
        )


class ExternalServiceError(AppException):
    """Raised when external service (Stripe, OpenAI, etc) fails.
    
    Provides context for third-party integration failures.
    """
    
    def __init__(
        self,
        service_name: str,
        operation: str,
        original_error: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize ExternalServiceError.
        
        Args:
            service_name: Name of external service (e.g., 'Stripe', 'OpenAI')
            operation: Operation that failed (e.g., 'create_charge')
            original_error: Error from the external service
            details: Additional context
        """
        message = f"{service_name} {operation} failed"
        if original_error:
            message += f": {original_error}"
        
        error_details = details or {}
        error_details.update({
            "service": service_name,
            "operation": operation,
            "external_error": original_error
        })
        super().__init__(
            message=message,
            code="EXTERNAL_SERVICE_ERROR",
            details=error_details,
            status_code=status.HTTP_502_BAD_GATEWAY
        )


class DatabaseError(AppException):
    """Raised when database operation fails.
    
    Wraps SQLAlchemy exceptions with more context.
    """
    
    def __init__(
        self,
        operation: str,
        entity_type: Optional[str] = None,
        original_error: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize DatabaseError.
        
        Args:
            operation: Database operation (e.g., 'create', 'update', 'delete')
            entity_type: Type of entity (e.g., 'User', 'Payment')
            original_error: Original SQLAlchemy error message
            details: Additional context
        """
        entity_part = f" {entity_type}" if entity_type else ""
        message = f"Database {operation} failed for{entity_part}"
        if original_error:
            message += f": {original_error}"
        
        error_details = details or {}
        error_details.update({
            "operation": operation,
            "entity_type": entity_type,
            "db_error": original_error
        })
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            details=error_details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class InvalidStateError(AppException):
    """Raised when operation violates state constraints.
    
    Examples:
    - Cannot activate already active subscription
    - Cannot refund completed payment
    - Cannot delete business with active subscriptions
    """
    
    def __init__(
        self,
        message: str,
        current_state: Optional[str] = None,
        required_state: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize InvalidStateError.
        
        Args:
            message: Description of the state violation
            current_state: Current state of the resource
            required_state: Required state for operation
            details: Additional context
        """
        error_details = details or {}
        if current_state:
            error_details["current_state"] = current_state
        if required_state:
            error_details["required_state"] = required_state
        super().__init__(
            message=message,
            code="INVALID_STATE",
            details=error_details,
            status_code=status.HTTP_400_BAD_REQUEST
        )


def http_exception_from_app_exception(exc: AppException) -> HTTPException:
    """Convert AppException to FastAPI HTTPException.
    
    Args:
        exc: The AppException to convert
        
    Returns:
        HTTPException ready for FastAPI response
    """
    return HTTPException(
        status_code=exc.status_code,
        detail={
            "error": exc.code,
            "message": exc.message,
            "details": exc.details
        }
    )
