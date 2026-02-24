# Error Handling Best Practices - Code Examples

This file contains practical examples for using the new error handling system in different scenarios.

## 1. Service Layer Error Handling

### Example 1: Validation in Service Methods

Bad (Old Way):
```python
def update_user_profile(db: Session, user_id: UUID, data: dict) -> User:
    if not data.get("email"):
        raise ValueError("Email is required")  # Generic error
    
    user = db.query(User).get(user_id)
    if not user:
        return None  # Silent failure
    
    user.email = data["email"]
    db.commit()
    return user
```

Good (New Way):
```python
from app.core.exceptions import ValidationError, ResourceNotFoundError

def update_user_profile(db: Session, user_id: UUID, data: dict) -> User:
    try:
        # Validate input
        if not data.get("email"):
            raise ValidationError(
                message="Email is required",
                field="email",
                details={
                    "constraint": "required",
                    "received": None
                }
            )
        
        if "@" not in data["email"]:
            raise ValidationError(
                message="Invalid email format",
                field="email",
                details={
                    "constraint": "must contain @",
                    "received": data["email"],
                    "pattern": "^[\\w\\.-]+@[\\w\\.-]+\\.\\w+$"
                }
            )
        
        # Find resource
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ResourceNotFoundError(
                resource_type="User",
                resource_id=str(user_id),
                details={"operation": "update_profile"}
            )
        
        # Update
        user.email = data["email"]
        db.commit()
        db.refresh(user)
        
        logger.info(f"Profile updated for user {user_id}")
        return user
        
    except (ValidationError, ResourceNotFoundError):
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise DatabaseError(
            operation="update",
            entity_type="User",
            original_error=str(e),
            details={
                "user_id": str(user_id),
                "attempted_email": data.get("email")
            }
        )
```

Benefits:
- ✅ Clear validation errors with field information
- ✅ Specific resource not found error
- ✅ Transaction safety with rollback
- ✅ Contextual logging with operation details

---

### Example 2: State Validation in Service

Bad (Old Way):
```python
def cancel_subscription(db: Session, subscription_id: UUID) -> Subscription:
    subscription = db.query(Subscription).get(subscription_id)
    subscription.status = SubscriptionStatus.CANCELED
    db.commit()  # What if it was already CANCELED?
    return subscription
```

Good (New Way):
```python
from app.core.exceptions import InvalidStateError

def cancel_subscription(db: Session, subscription_id: UUID) -> Subscription:
    try:
        subscription = db.query(Subscription).filter(
            Subscription.id == subscription_id
        ).first()
        
        # Validate resource exists
        if not subscription:
            raise ResourceNotFoundError(
                resource_type="Subscription",
                resource_id=str(subscription_id)
            )
        
        # Validate state transition
        if subscription.status == SubscriptionStatus.CANCELED:
            raise InvalidStateError(
                message="Cannot cancel an already cancelled subscription",
                current_state=subscription.status.value,
                required_state="ACTIVE or PENDING",
                details={
                    "subscription_id": str(subscription_id),
                    "cancellation_date": subscription.canceled_at
                }
            )
        
        # Perform cancellation
        subscription.status = SubscriptionStatus.CANCELED
        subscription.canceled_at = datetime.utcnow()
        
        db.commit()
        db.refresh(subscription)
        
        logger.info(f"Subscription {subscription_id} cancelled")
        return subscription
        
    except (ResourceNotFoundError, InvalidStateError):
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise DatabaseError(
            operation="cancel",
            entity_type="Subscription",
            original_error=str(e),
            details={"subscription_id": str(subscription_id)}
        )
```

Benefits:
- ✅ Clear state validation with current and required states
- ✅ Prevents silent failures
- ✅ Audit trail with cancellation date
- ✅ Detailed error context for debugging

---

### Example 3: External Service Integration

Bad (Old Way):
```python
def process_payment_with_stripe(payment_id: UUID) -> Payment:
    payment = db.query(Payment).get(payment_id)
    
    try:
        charge = stripe.Charge.create(
            amount=int(payment.amount * 100),
            currency="usd",
            source="tok_visa"
        )
        payment.stripe_charge_id = charge.id
        db.commit()
        return payment
    except Exception as e:
        logger.error(f"Error: {e}")  # What happened? What service?
        raise
```

Good (New Way):
```python
from app.core.exceptions import ExternalServiceError, DatabaseError

def process_payment_with_stripe(db: Session, payment_id: UUID) -> Payment:
    try:
        # Fetch payment
        payment = db.query(Payment).filter(
            Payment.id == payment_id
        ).first()
        
        if not payment:
            raise ResourceNotFoundError(
                resource_type="Payment",
                resource_id=str(payment_id)
            )
        
        # Validate payment state
        if payment.status != PaymentStatus.PENDING:
            raise InvalidStateError(
                message="Payment already processed",
                current_state=payment.status.value,
                required_state="PENDING"
            )
        
        # Call Stripe with error handling
        try:
            logger.info(f"Processing payment {payment_id} with Stripe")
            charge = stripe.Charge.create(
                amount=int(payment.amount * 100),
                currency="usd",
                source=payment.stripe_token,
                metadata={"payment_id": str(payment_id)}
            )
            
            # Update payment
            payment.stripe_charge_id = charge.id
            payment.status = PaymentStatus.COMPLETED
            payment.processed_at = datetime.utcnow()
            
            db.commit()
            db.refresh(payment)
            
            logger.info(f"Payment {payment_id} processed successfully")
            return payment
            
        except stripe.error.CardError as e:
            # Card was declined
            raise ExternalServiceError(
                service_name="Stripe",
                operation="charge_create",
                original_error=str(e.user_message),
                details={
                    "error_type": "CardError",
                    "error_code": e.code,
                    "status_code": e.http_status,
                    "payment_id": str(payment_id)
                }
            )
        except stripe.error.APIConnectionError as e:
            # Network error
            raise ExternalServiceError(
                service_name="Stripe",
                operation="charge_create",
                original_error="Connection failed to Stripe API",
                details={
                    "error_type": "APIConnectionError",
                    "payment_id": str(payment_id),
                    "retry": True
                }
            )
        except stripe.error.StripeError as e:
            # Other Stripe errors
            raise ExternalServiceError(
                service_name="Stripe",
                operation="charge_create",
                original_error=str(e),
                details={
                    "error_type": type(e).__name__,
                    "payment_id": str(payment_id)
                }
            )
    
    except (ResourceNotFoundError, InvalidStateError, ExternalServiceError):
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise DatabaseError(
            operation="process_payment",
            entity_type="Payment",
            original_error=str(e),
            details={"payment_id": str(payment_id)}
        )
```

Benefits:
- ✅ Clear distinction between Stripe errors and DB errors
- ✅ Specific error types (CardError vs ConnectionError) for handling
- ✅ Retry guidance in details (for transient errors)
- ✅ Full context for debugging failed payments

---

## 2. Route Layer Error Handling

### Example 1: Protected Routes with Authorization

Bad (Old Way):
```python
@router.post("/subscriptions/{id}/cancel")
def cancel_subscription(id: UUID, current_user: User):
    subscription = db.query(Subscription).get(id)
    
    if subscription.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")  # Generic
    
    return service.cancel_subscription(db, id)
```

Good (New Way):
```python
from app.core.exceptions import AccessDeniedError

@router.post("/subscriptions/{id}/cancel")
def cancel_subscription(
    id: UUID,
    current_user: User,
    db: Session = Depends(get_db)
):
    """
    Cancel a subscription.
    
    Requires:
    - User must own the subscription
    - Subscription must be ACTIVE or PENDING
    
    Args:
        id: Subscription ID to cancel
        current_user: Authenticated user
        db: Database session
    
    Returns:
        Updated subscription with CANCELED status
    
    Raises:
        ResourceNotFoundError: Subscription not found
        AccessDeniedError: User doesn't own subscription
        InvalidStateError: Subscription already canceled
    """
    try:
        # Check ownership
        subscription = db.query(Subscription).filter(
            Subscription.id == id
        ).first()
        
        if not subscription:
            raise ResourceNotFoundError(
                resource_type="Subscription",
                resource_id=str(id)
            )
        
        if subscription.user_id != current_user.id:
            raise AccessDeniedError(
                action="cancel",
                resource_type="subscription",
                details={
                    "subscription_id": str(id),
                    "owner_id": str(subscription.user_id),
                    "requester_id": str(current_user.id)
                }
            )
        
        # Cancel subscription
        return subscription_service.cancel_subscription(db, id)
        
    except (ResourceNotFoundError, AccessDeniedError, InvalidStateError):
        raise
    except Exception as e:
        logger.error(f"Unexpected error canceling subscription: {e}")
        raise
```

Response examples:

Success (200):
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "status": "CANCELED",
  "canceled_at": "2024-01-15T10:30:00Z"
}
```

Not found (404):
```json
{
  "status_code": 404,
  "error_code": "NOT_FOUND",
  "message": "Subscription with ID '...' not found",
  "details": {
    "resource_type": "Subscription",
    "resource_id": "..."
  }
}
```

Not authorized (403):
```json
{
  "status_code": 403,
  "error_code": "FORBIDDEN",
  "message": "You don't have permission to cancel this subscription",
  "details": {
    "action": "cancel",
    "resource_type": "subscription",
    "owner_id": "...",
    "requester_id": "..."
  }
}
```

---

### Example 2: Validation in Route

Bad (Old Way):
```python
@router.post("/payments")
def create_payment(data: PaymentCreate, current_user: User):
    # Validation happens implicitly in Pydantic
    # But business logic validation doesn't happen until service
    return payment_service.create_payment(db, data, current_user.id)
```

Good (New Way):
```python
@router.post("/payments")
def create_payment(
    data: PaymentCreate,
    current_user: User,
    db: Session = Depends(get_db)
):
    """
    Create a new payment.
    
    Business logic validation:
    - Amount must be > 0 and < 1000000
    - Plan must exist
    - User can have max 3 active payments
    
    Args:
        data: Payment creation data (validated by Pydantic)
        current_user: Authenticated user
        db: Database session
    
    Returns:
        Created payment with PENDING status
    
    Raises:
        ValidationError: Invalid amount or too many active payments
        ResourceNotFoundError: Plan doesn't exist
    """
    try:
        # Pydantic validation happens automatically on 'data'
        # Add business logic validation here
        
        if data.amount <= 0 or data.amount > 1000000:
            raise ValidationError(
                message="Payment amount must be between $0.01 and $1,000,000",
                field="amount",
                details={
                    "min": 0.01,
                    "max": 1000000,
                    "received": data.amount
                }
            )
        
        # Check active payments
        active_count = db.query(Payment).filter(
            Payment.user_id == current_user.id,
            Payment.status == PaymentStatus.PENDING
        ).count()
        
        if active_count >= 3:
            raise ValidationError(
                message="Maximum 3 active payments allowed",
                field="payment_limit",
                details={
                    "current_active": active_count,
                    "max_allowed": 3
                }
            )
        
        # Create payment
        return payment_service.create_payment(
            db,
            data,
            current_user.id
        )
        
    except (ValidationError, ResourceNotFoundError):
        raise
    except Exception as e:
        logger.error(f"Error creating payment: {e}")
        raise
```

Client error response (422):
```json
{
  "status_code": 422,
  "error_code": "VALIDATION_ERROR",
  "message": "Payment amount must be between $0.01 and $1,000,000",
  "details": {
    "field": "amount",
    "constraint": "range",
    "min": 0.01,
    "max": 1000000,
    "received": -100
  }
}
```

---

## 3. Error Handling in Testing

### Example: Testing Error Scenarios

```python
import pytest
from fastapi.testclient import TestClient
from app.core.exceptions import ValidationError

@pytest.fixture
def client():
    from main import app
    return TestClient(app)

def test_create_payment_validates_amount(client, user_token):
    """Test that payment validation rejects negative amounts."""
    response = client.post(
        "/payments",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"amount": -100, "plan_id": "valid-uuid"}
    )
    
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"
    assert "amount" in data["details"]["field"]
    assert data["details"]["received"] == -100

def test_cancel_subscription_not_found(client, user_token):
    """Test that canceling non-existent subscription returns 404."""
    import uuid
    fake_id = uuid.uuid4()
    
    response = client.post(
        f"/subscriptions/{fake_id}/cancel",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    assert response.status_code == 404
    data = response.json()
    assert data["error_code"] == "NOT_FOUND"
    assert data["details"]["resource_type"] == "Subscription"
    assert data["details"]["resource_id"] == str(fake_id)

def test_cancel_subscription_unauthorized(client, other_user_token):
    """Test that user can't cancel others' subscriptions."""
    # Create subscription as first user
    sub = create_test_subscription(user_id="user1")
    
    # Try to cancel as different user
    response = client.post(
        f"/subscriptions/{sub.id}/cancel",
        headers={"Authorization": f"Bearer {other_user_token}"}
    )
    
    assert response.status_code == 403
    data = response.json()
    assert data["error_code"] == "FORBIDDEN"
    assert "You don't have permission" in data["message"]

def test_payment_service_raises_external_service_error(mocker):
    """Test that Stripe errors are properly wrapped."""
    from app.services.billing.payment_service import process_payment_with_stripe
    from app.core.exceptions import ExternalServiceError
    import stripe
    
    # Mock Stripe to raise CardError
    mocker.patch.object(
        stripe.Charge,
        "create",
        side_effect=stripe.error.CardError(
            message="Card declined",
            param="card",
            code="card_declined"
        )
    )
    
    with pytest.raises(ExternalServiceError) as exc_info:
        process_payment_with_stripe(db, payment_id)
    
    error = exc_info.value
    assert error.code == "EXTERNAL_SERVICE_ERROR"
    assert error.details["service_name"] == "Stripe"
    assert error.details["error_type"] == "CardError"
```

---

## 4. Logging with Error Context

### Example: Structured Logging

```python
import logging
from typing import Optional
from uuid import UUID

logger = logging.getLogger(__name__)

def log_payment_processing(
    payment_id: UUID,
    user_id: UUID,
    amount: float,
    status: str,
    error: Optional[Exception] = None
):
    """Log payment processing with full context."""
    
    context = {
        "payment_id": str(payment_id),
        "user_id": str(user_id),
        "amount": amount,
        "status": status,
    }
    
    if error:
        if hasattr(error, 'details'):
            context.update(error.details)
        
        logger.error(
            f"Payment processing failed: {error.message}",
            extra=context,
            exc_info=True
        )
    else:
        logger.info(
            f"Payment {payment_id} processed successfully",
            extra=context
        )
```

Log output:
```
ERROR | Payment processing failed: Card declined
  payment_id: 550e8400-e29b-41d4-a716-446655440000
  user_id: 660e8400-e29b-41d4-a716-446655440001
  amount: 99.99
  status: FAILED
  service_name: Stripe
  error_type: CardError
  error_code: card_declined
  traceback: [...]
```

---

## Summary of Best Practices

1. **Always import specific exception classes** - Not generic `Exception`
2. **Validate input before operations** - Raise `ValidationError` early
3. **Check resource existence immediately** - Raise `ResourceNotFoundError`
4. **Validate state transitions** - Raise `InvalidStateError` for constraint violations
5. **Wrap external service calls** - Raise `ExternalServiceError` with details
6. **Always rollback on error** - Database consistency
7. **Include context in details** - IDs, field names, current/required states
8. **Log appropriately** - Structured logs with context
9. **Write error scenario tests** - Test happy path AND error paths
10. **Use middleware for global handling** - Don't repeat error handling in every route
