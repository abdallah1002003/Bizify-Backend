import pytest
from fastapi import status, HTTPException
from app.core.exceptions import (
    AppException,
    ValidationError,
    ResourceNotFoundError,
    AuthenticationError,
    BadRequestError,
    AccessDeniedError,
    ConflictError,
    ExternalServiceError,
    DatabaseError,
    InvalidStateError,
    http_exception_from_app_exception,
)

def test_app_exception_basic():
    exc = AppException("msg", code="ERR", status_code=400, details={"foo": "bar"})
    assert exc.message == "msg"
    assert exc.code == "ERR"
    assert exc.status_code == 400
    assert exc.details == {"foo": "bar"}
    assert str(exc) == "msg"

def test_validation_error():
    # Case: no field
    exc1 = ValidationError("invalid")
    assert exc1.code == "VALIDATION_ERROR"
    assert exc1.status_code == 422
    assert exc1.details == {}
    
    # Case: with field
    exc2 = ValidationError("invalid", field="email")
    assert exc2.details == {"field": "email"}

def test_resource_not_found_error():
    exc = ResourceNotFoundError("User", "uuid-123", details={"extra": "data"})
    assert exc.status_code == 404
    assert "User with ID 'uuid-123' not found" in exc.message
    assert exc.details["resource_type"] == "User"
    assert exc.details["resource_id"] == "uuid-123"
    assert exc.details["extra"] == "data"

def test_authentication_error():
    exc = AuthenticationError("Auth failed")
    assert exc.status_code == 401
    assert exc.code == "AUTHENTICATION_ERROR"

def test_bad_request_error():
    exc = BadRequestError("Bad request")
    assert exc.status_code == 400
    assert exc.code == "BAD_REQUEST"

def test_access_denied_error():
    # Case: no resource_type
    exc1 = AccessDeniedError("delete")
    assert exc1.status_code == 403
    assert exc1.message == "Access denied: cannot delete"
    
    # Case: with resource_type
    exc2 = AccessDeniedError("update", resource_type="User")
    assert exc2.message == "Access denied: cannot update User"
    assert exc2.details["resource_type"] == "User"

def test_conflict_error():
    # Case: basic
    exc1 = ConflictError("conflict")
    assert exc1.status_code == 409
    
    # Case: with field and value
    exc2 = ConflictError("conflict", conflict_field="email", existing_value="test@ex.com")
    assert exc2.details["conflict_field"] == "email"
    assert exc2.details["existing_value"] == "test@ex.com"

def test_external_service_error():
    # Case: no original error
    exc1 = ExternalServiceError("Stripe", "charge")
    assert exc1.status_code == 502
    assert exc1.message == "Stripe charge failed"
    
    # Case: with original error
    exc2 = ExternalServiceError("OpenAI", "complete", original_error="API Down")
    assert exc2.message == "OpenAI complete failed: API Down"
    assert exc2.details["external_error"] == "API Down"

def test_database_error():
    # Case: no entity_type, no original_error
    exc1 = DatabaseError("save")
    assert exc1.status_code == 500
    assert exc1.message == "Database save failed for"
    
    # Case: complete
    exc2 = DatabaseError("update", entity_type="User", original_error="unique constraint")
    assert exc2.message == "Database update failed for User: unique constraint"
    assert exc2.details["entity_type"] == "User"
    assert exc2.details["db_error"] == "unique constraint"

def test_invalid_state_error():
    # Case: basic
    exc1 = InvalidStateError("invalid state")
    assert exc1.status_code == 400
    
    # Case: with current/required state
    exc2 = InvalidStateError("violation", current_state="active", required_state="inactive")
    assert exc2.details["current_state"] == "active"
    assert exc2.details["required_state"] == "inactive"

def test_http_exception_conversion():
    app_exc = AppException("error msg", code="CUSTOM_CODE", status_code=418, details={"a": 1})
    http_exc = http_exception_from_app_exception(app_exc)
    
    assert isinstance(http_exc, HTTPException)
    assert http_exc.status_code == 418
    assert http_exc.detail["error"] == "CUSTOM_CODE"
    assert http_exc.detail["message"] == "error msg"
    assert http_exc.detail["details"] == {"a": 1}
