# ruff: noqa
# type: ignore
"""
Payment CRUD operations and payment processing.
"""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Payment, Usage
from app.models.enums import SubscriptionStatus, PaymentStatus
from app.services.billing.crud_utils import get_by_id, list_records
from app.services.billing import subscription_service
from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates
from app.core.exceptions import (
    ResourceNotFoundError,
    ValidationError,
    InvalidStateError,
    DatabaseError
)

logger = logging.getLogger(__name__)


# ----------------------------
# Payment
# ----------------------------

def get_payment(db: Session, id: UUID) -> Optional[Payment]:
    """Retrieve a single payment by its unique ID.
    
    Args:
        db: Database session
        id: The payment UUID to retrieve
        
    Returns:
        The Payment object if found, None otherwise
    """
    return get_by_id(db, Payment, id)


def get_payments(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
) -> List[Payment]:
    """Retrieve payments with pagination and optional user filtering.
    
    Args:
        db: Database session
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        user_id: Optional filter by user ID
        
    Returns:
        List of Payment objects
    """
    return list_records(
        db,
        Payment,
        skip=skip,
        limit=limit,
        filters={"user_id": user_id},
    )


def create_payment(db: Session, obj_in: Any) -> Payment:
    """Create a new payment record with error handling.
    
    Args:
        db: Database session
        obj_in: Payment creation data (dict or Pydantic model)
        
    Returns:
        The created Payment object
        
    Raises:
        Exception: If database operation fails
    """
    try:
        db_obj = Payment(**_to_update_dict(obj_in))
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        logger.info(f"Created payment {db_obj.id}")
        return db_obj
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating payment: {e}")
        raise


def update_payment(db: Session, db_obj: Payment, obj_in: Any) -> Payment:
    """Update mutable fields on a payment."""

    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_payment(db: Session, id: UUID) -> Optional[Payment]:
    """Delete a payment by id."""

    db_obj = get_payment(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


def process_payment(
    db: Session,
    subscription_id: UUID,
    amount: float,
    method_id: UUID,
    currency: str = "usd",
) -> Payment:
    """Create a successful payment and activate the related subscription.
    
    This function processes a payment by:
    1. Verifying the subscription exists and is in a valid state
    2. Creating a Payment record with COMPLETED status
    3. Activating the subscription
    4. Extending subscription end date by 30 days
    
    Args:
        db: Database session
        subscription_id: UUID of the subscription being paid for
        amount: Payment amount in the specified currency (must be > 0)
        method_id: UUID of the payment method used
        currency: Currency code (default: 'usd')
        
    Returns:
        The created Payment object with complete details
        
    Raises:
        ValidationError: If amount <= 0 or subscription_id is invalid
        ResourceNotFoundError: If subscription is not found
        InvalidStateError: If subscription is in invalid state for payment
        DatabaseError: If database operation fails
    """
    try:
        # Validate amount
        if amount <= 0:
            raise ValidationError(
                message=f"Payment amount must be positive, got {amount}",
                field="amount",
                details={"provided_amount": amount}
            )
        
        # Fetch subscription
        subscription = subscription_service.get_subscription(db, id=subscription_id)
        if subscription is None:
            raise ResourceNotFoundError(
                resource_type="Subscription",
                resource_id=str(subscription_id),
                details={"operation": "process_payment"}
            )
        
        # Validate subscription state
        if subscription.status == SubscriptionStatus.CANCELED:
            raise InvalidStateError(
                message=f"Cannot process payment for canceled subscription {subscription_id}",
                current_state=str(subscription.status),
                required_state="PENDING or ACTIVE",
                details={"subscription_id": str(subscription_id)}
            )

        db_payment = Payment(
            user_id=subscription.user_id,
            subscription_id=subscription_id,
            payment_method_id=method_id,
            amount=amount,
            currency=currency,
            status=PaymentStatus.COMPLETED,
        )
        db.add(db_payment)

        subscription.status = SubscriptionStatus.ACTIVE
        base_end = subscription.end_date or _utc_now()
        subscription.end_date = base_end + timedelta(days=30)

        db.commit()
        db.refresh(db_payment)
        logger.info(f"Processed payment {db_payment.id} for subscription {subscription_id}: ${amount} {currency}")
        return db_payment
    except (ValidationError, ResourceNotFoundError, InvalidStateError):
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing payment for subscription {subscription_id}: {e}")
        raise DatabaseError(
            operation="process_payment",
            entity_type="Payment",
            original_error=str(e),
            details={
                "subscription_id": str(subscription_id),
                "amount": amount,
                "currency": currency
            }
        )


def process_subscription_payment(db: Session, subscription_id, amount: float, payment_method_id):
    """Backward-compatible wrapper around `process_payment`."""
    return process_payment(
        db,
        subscription_id=subscription_id,
        amount=amount,
        method_id=payment_method_id,
    )


def handle_payment_reversal(db: Session, payment_id: UUID) -> None:
    """Reverse a payment and cancel the linked subscription if present.
    
    This function:
    1. Marks the payment as REFUNDED
    2. Cancels the related subscription (if exists)
    3. Sets usage limits to 0 for the user
    
    Args:
        db: Database session
        payment_id: UUID of the payment to reverse
        
    Returns:
        None
        
    Raises:
        Exception: If database operation fails
    """
    try:
        payment = get_payment(db, id=payment_id)
        if payment is None:
            logger.warning(f"Payment {payment_id} not found for reversal")
            return

        payment.status = PaymentStatus.REFUNDED
        if payment.subscription_id is not None:
            subscription = subscription_service.get_subscription(db, id=payment.subscription_id)
            if subscription is not None:
                subscription.status = SubscriptionStatus.CANCELED
                db.query(Usage).filter(Usage.user_id == subscription.user_id).update({"limit_value": 0})

        db.commit()
        logger.info(f"Reversed payment {payment_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error reversing payment {payment_id}: {e}")
        raise
