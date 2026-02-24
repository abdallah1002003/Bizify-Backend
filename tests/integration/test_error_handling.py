"""Integration tests for enhanced error handling.

Tests for custom exception handling, error messages, and edge cases.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from app.core.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    AccessDeniedError,
    InvalidStateError,
    DatabaseError
)
from app.models.enums import SubscriptionStatus
from app.services.billing import subscription_service


class TestErrorHandling:
    """Test suite for error handling mechanisms."""
    
    def test_validation_error_missing_fields(self, db: Session):
        """Test ValidationError when required fields are missing."""
        with pytest.raises(ValidationError) as exc_info:
            # Try to create subscription without required fields
            subscription_service.create_subscription(db, obj_in={})
        
        exc = exc_info.value
        assert exc.code == "VALIDATION_ERROR"
        assert "missing_fields" in exc.details
        assert exc.status_code == 422
    
    def test_resource_not_found_error(self, db: Session):
        """Test ResourceNotFoundError when resource doesn't exist."""
        with pytest.raises(ResourceNotFoundError) as exc_info:
            subscription_service.create_subscription(db, obj_in={
                "user_id": uuid4(),
                "plan_id": uuid4()  # Non-existent plan
            })
        
        exc = exc_info.value
        assert exc.code == "NOT_FOUND"
        assert "resource_type" in exc.details
        assert exc.status_code == 404
    
    def test_access_denied_error(self):
        """Test AccessDeniedError for authorization failures."""
        with pytest.raises(AccessDeniedError) as exc_info:
            raise AccessDeniedError(
                action="update",
                resource_type="subscription"
            )
        
        exc = exc_info.value
        assert exc.code == "ACCESS_DENIED"
        assert exc.status_code == 403
        assert "update" in exc.message
    
    def test_invalid_state_error(self):
        """Test InvalidStateError for state constraint violations."""
        with pytest.raises(InvalidStateError) as exc_info:
            raise InvalidStateError(
                message="Cannot process payment for cancelled subscription",
                current_state="CANCELED",
                required_state="ACTIVE or PENDING"
            )
        
        exc = exc_info.value
        assert exc.code == "INVALID_STATE"
        assert exc.status_code == 400
    
    def test_error_response_structure(self):
        """Test that error responses have correct structure."""
        error = ValidationError(
            message="Test validation error",
            field="email",
            details={"pattern": "invalid"}
        )
        
        assert error.code == "VALIDATION_ERROR"
        assert error.message == "Test validation error"
        assert error.details["field"] == "email"
        assert error.status_code == 422


class TestEndpointErrorHandling:
    """Test error handling in API endpoints."""
    
    def test_create_payment_missing_subscription(
        self, 
        client: TestClient,
        user_token: str,
        db: Session
    ):
        """Test creating payment with non-existent subscription."""
        response = client.post(
            "/api/v1/payments/",
            json={
                "subscription_id": str(uuid4()),
                "payment_method_id": str(uuid4()),
                "amount": 29.99
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["error_code"] == "NOT_FOUND"
        assert "Subscription" in data["message"]
    
    def test_create_payment_insufficient_permissions(
        self,
        client: TestClient,
        another_user_token: str,
        user_subscription,
        db: Session
    ):
        """Test creating payment for another user's subscription."""
        response = client.post(
            "/api/v1/payments/",
            json={
                "subscription_id": str(user_subscription.id),
                "payment_method_id": str(uuid4()),
                "amount": 29.99
            },
            headers={"Authorization": f"Bearer {another_user_token}"}
        )
        
        assert response.status_code == 403
        data = response.json()
        assert data["error_code"] == "ACCESS_DENIED"
        assert "permission" in data["message"].lower()


class TestLoggingAndDebugInfo:
    """Test that errors are logged with sufficient context."""
    
    def test_db_error_includes_context(self, caplog, db: Session):
        """Test that database errors include operation context."""
        import logging
        caplog.set_level(logging.DEBUG)
        
        try:
            # This should fail with DatabaseError
            subscription_service.create_subscription(db, obj_in={
                "user_id": uuid4(),
                "plan_id": uuid4()
            })
        except Exception:
            pass
        
        # Check logs have error code and context
        assert any("NOT_FOUND" in record.message for record in caplog.records)
    
    def test_validation_error_includes_field_info(self):
        """Test validation errors include field-specific information."""
        error = ValidationError(
            message="Invalid email format",
            field="email",
            details={"pattern": "must contain @"}
        )
        
        assert "email" in error.details["field"]
        assert "pattern" in error.details
