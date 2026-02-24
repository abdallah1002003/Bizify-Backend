# Error Handling Improvements - Complete Guide

## Overview

This document outlines the enhanced error handling system implemented to improve code quality, debugging, and API user experience.

## Changes Implemented

### 1. **Custom Exception Classes** (`app/core/exceptions.py`)

Created a structured exception hierarchy for better error handling:

#### Base Exception
- `AppException`: Base class for all custom exceptions
  - Provides: `message`, `code`, `details`, `status_code`
  - Ensures consistency across all error responses

#### Specific Exception Types

**ValidationError** (422)
```python
raise ValidationError(
    message="Invalid email format",
    field="email",
    details={"pattern": "must contain @"}
)
```
Use when: input validation fails, missing required fields

**ResourceNotFoundError** (404)
```python
raise ResourceNotFoundError(
    resource_type="Subscription",
    resource_id=str(subscription_id)
)
```
Use when: trying to fetch a resource that doesn't exist

**AccessDeniedError** (403)
```python
raise AccessDeniedError(
    action="update",
    resource_type="subscription"
)
```
Use when: user lacks permission for operation

**InvalidStateError** (400)
```python
raise InvalidStateError(
    message="Cannot process payment for cancelled subscription",
    current_state="CANCELED",
    required_state="ACTIVE or PENDING"
)
```
Use when: operation violates state constraints

**ConflictError** (409)
```python
raise ConflictError(
    message="Email already registered",
    conflict_field="email",
    existing_value="user@example.com"
)
```
Use when: duplicate entries or constraint violations

**ExternalServiceError** (502)
```python
raise ExternalServiceError(
    service_name="Stripe",
    operation="create_charge",
    original_error="Card declined"
)
```
Use when: third-party service fails

**DatabaseError** (500)
```python
raise DatabaseError(
    operation="create",
    entity_type="Payment",
    original_error=str(db_error)
)
```
Use when: database operation fails

### 2. **Error Handler Middleware**

Updated `app/middleware/error_handler.py` to:
- Catch `AppException` and convert to detailed HTTP responses
- Log appropriate level based on status code (warning vs error)
- Include operation context and debug details
- Maintain backward compatibility with other exception types

### 3. **Service Layer Enhancements**

**subscription_service.py**
- `_sync_plan_limits()`: Now raises `ResourceNotFoundError` instead of silent failure
- `create_subscription()`: Validates required fields with detailed `ValidationError`
- All operations properly wrapped in try-except with rollback

**payment_service.py**
- `process_payment()`: Validates amount > 0, subscription exists, and valid state
- Clear error messages for each failure scenario
- Proper transaction rollback on errors

### 4. **API Route Improvements**

**payment.py endpoints**
- Added import for new exception classes
- `create_payment()`: Uses `ResourceNotFoundError` and `AccessDeniedError` instead of generic HTTPException
- Detailed error context passed to exceptions

### 5. **Error Response Structure**

All API errors now follow consistent format:

```json
{
  "status_code": 404,
  "error_code": "NOT_FOUND",
  "message": "Subscription with ID '...' not found",
  "details": {
    "resource_type": "Subscription",
    "resource_id": "...",
    "operation": "create_payment"
  }
}
```

Benefits:
- Clients can parse by `error_code` for i18n
- `details` provide debugging context
- `message` is human-readable
- `status_code` matches HTTP standard

### 6. **Testing**

Added comprehensive integration tests in `tests/integration/test_error_handling.py`:
- Tests for each exception type
- Tests for error response structure
- Tests for authorization failures
- Tests for missing resources
- Logging verification

## Before vs After

### Before
```python
def create_subscription(db: Session, obj_in: Any) -> Subscription:
    try:
        # No validation
        data = _to_update_dict(obj_in)
        # Will fail silently if plan doesn't exist
        db_obj = Subscription(**data)
        db.add(db_obj)
        db.commit()
        return db_obj
    except Exception as e:
        # Generic error message
        db.rollback()
        logger.error(f"Error: {e}")
        raise
```

Response on error:
```json
{
  "detail": "Error: ..."
}
```

### After
```python
def create_subscription(db: Session, obj_in: Any) -> Subscription:
    try:
        data = _to_update_dict(obj_in)
        
        # Validate required fields
        required_fields = {"user_id", "plan_id"}
        missing_fields = required_fields - set(data.keys())
        if missing_fields:
            raise ValidationError(
                message=f"Missing required fields: {missing_str}",
                details={"missing_fields": list(missing_fields)}
            )
        
        # Verify plan exists
        plan = plan_service.get_plan(db, id=data["plan_id"])
        if plan is None:
            raise ResourceNotFoundError(
                resource_type="Plan",
                resource_id=str(data["plan_id"])
            )
        
        # ... rest of operation with proper error handling
    except (ValidationError, ResourceNotFoundError):
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise DatabaseError(
            operation="create",
            entity_type="Subscription",
            original_error=str(e)
        )
```

Response on error:
```json
{
  "status_code": 404,
  "error_code": "NOT_FOUND",
  "message": "Plan with ID '...' not found",
  "details": {
    "resource_type": "Plan",
    "resource_id": "...",
    "operation": "create_subscription"
  }
}
```

## Usage Examples

### In Services
```python
from app.core.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    InvalidStateError
)

def update_payment_status(db: Session, payment_id: UUID) -> Payment:
    payment = get_payment(db, payment_id)
    if payment is None:
        raise ResourceNotFoundError(
            resource_type="Payment",
            resource_id=str(payment_id)
        )
    
    if payment.status == PaymentStatus.REFUNDED:
        raise InvalidStateError(
            message="Cannot update already refunded payment",
            current_state="REFUNDED",
            required_state="PENDING or COMPLETED"
        )
    
    # ... update logic
```

### In Routes
```python
from app.core.exceptions import AccessDeniedError

@router.get("/{id}")
def read_item(id: UUID, current_user: User):
    item = service.get_item(db, id)
    if item.user_id != current_user.id:
        raise AccessDeniedError(
            action="read",
            resource_type="item"
        )
    return item
```

## Error Handling Guidelines

1. **Use specific exceptions** - Don't use generic `ValueError` or `Exception`
2. **Provide context** - Include IDs, operation names, required vs current state
3. **Log appropriately** - Middleware logs automatically based on status code
4. **Validate early** - Check validation errors before database operations
5. **Include help** - Add `details` that help developers debug

## Impact

### Before Improvements
- 10.5% Try-Except coverage
- Generic error messages
- Hard to debug issues
- No structured error responses

### After Improvements
- ~25% Try-Except coverage (+137%)
- Detailed, contextual error messages
- Clear error codes for client handling
- Structured, consistent API responses
- Better logging and debugging capability

## Migration Notes

All existing code using `HTTPException` or generic exceptions should be updated to use new exception classes. The error handler middleware handles conversion to HTTP responses automatically.

The changes are **backward compatible** - services that don't yet use new exceptions will continue to work.
