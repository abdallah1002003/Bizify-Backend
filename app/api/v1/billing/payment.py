# type: ignore
"""Payment API routes.

This module provides endpoints for managing payment records including:
- Listing payments with pagination
- Creating new payments
- Retrieving individual payments
- Updating payment details
- Deleting payments

All endpoints require authentication and enforce user ownership validation.
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from sqlalchemy.orm import Session
import app.models as models
from app.core.dependencies import get_current_active_user
from app.db.database import get_db
from app.schemas.billing.payment import PaymentCreate, PaymentUpdate, PaymentResponse
from app.services.billing import payment_method as payment_method_service
from app.services.billing import payment_service as service
from app.services.billing import subscription_service
from app.core.exceptions import AccessDeniedError, ResourceNotFoundError

router = APIRouter()


def _ensure_payment_owner(payment: models.Payment, current_user: models.User) -> None:
    """Verify that the current user owns the payment record.
    
    Args:
        payment: The payment record to verify
        current_user: The authenticated user
        
    Raises:
        HTTPException: 403 Forbidden if user doesn't own the payment
    """
    if payment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")


def _ensure_subscription_owner(
    subscription: models.Subscription, current_user: models.User
) -> None:
    """Verify that the current user owns the subscription.
    
    Args:
        subscription: The subscription to verify
        current_user: The authenticated user
        
    Raises:
        HTTPException: 403 Forbidden if user doesn't own the subscription
    """
    if subscription.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")


def _ensure_payment_method_owner(
    payment_method: models.PaymentMethod, current_user: models.User
) -> None:
    """Verify that the current user owns the payment method.
    
    Args:
        payment_method: The payment method to verify
        current_user: The authenticated user
        
    Raises:
        HTTPException: 403 Forbidden if user doesn't own the payment method
    """
    if payment_method.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")


@router.get("/", response_model=List[PaymentResponse])
def read_payments(
    skip: SkipParam = 0,
    limit: LimitParam = 20,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """List payments for current user with pagination.
    
    Query Parameters:
        skip: Number of records to skip (default: 0)
        limit: Number of records to return (default: 20, max: 100)
        
    Returns:
        List of Payment records for the authenticated user
    """
    return service.get_payments(db, skip=skip, limit=limit, user_id=current_user.id)

@router.post("/", response_model=PaymentResponse)
def create_payment(
    item_in: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Create a new payment record for the current user.
    
    This endpoint creates a payment by:
    1. Verifying the subscription belongs to the user
    2. Verifying the payment method belongs to the user
    3. Creating the payment record
    
    Args:
        item_in: Payment creation data (subscription_id, payment_method_id, amount)
        db: Database session
        current_user: The authenticated user
        
    Returns:
        The newly created Payment record
        
    Raises:
        HTTPException: 404 if subscription or payment method not found
        HTTPException: 403 if user doesn't own the subscription/payment method
        HTTPException: 422 if validation fails
    """
    # Verify subscription exists and belongs to current user
    subscription = subscription_service.get_subscription(db, id=item_in.subscription_id)
    if subscription is None:
        raise ResourceNotFoundError(
            resource_type="Subscription",
            resource_id=str(item_in.subscription_id)
        )
    
    if subscription.user_id != current_user.id:
        raise AccessDeniedError(
            action="create payment for",
            resource_type="subscription",
            details={"subscription_id": str(item_in.subscription_id)}
        )

    # Verify payment method exists and belongs to current user
    payment_method = payment_method_service.get_payment_method(db, id=item_in.payment_method_id)
    if payment_method is None:
        raise ResourceNotFoundError(
            resource_type="PaymentMethod",
            resource_id=str(item_in.payment_method_id)
        )
    
    if payment_method.user_id != current_user.id:
        raise AccessDeniedError(
            action="use",
            resource_type="payment method",
            details={"payment_method_id": str(item_in.payment_method_id)}
        )

    # Create payment
    data = item_in.model_dump()
    data["user_id"] = current_user.id
    return service.create_payment(db, obj_in=data)

@router.get("/{id}", response_model=PaymentResponse)
def read_payment(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Retrieve a specific payment by ID.
    
    Args:
        id: The UUID of the payment to retrieve
        db: Database session
        current_user: The authenticated user
        
    Returns:
        The Payment record
        
    Raises:
        HTTPException: 404 if payment not found
        HTTPException: 403 if user doesn't own the payment
    """
    db_obj = service.get_payment(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Payment not found")
    _ensure_payment_owner(db_obj, current_user)
    return db_obj

@router.put("/{id}", response_model=PaymentResponse)
def update_payment(
    id: UUID,
    item_in: PaymentUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Update an existing payment record.
    
    Args:
        id: The UUID of the payment to update
        item_in: Updated payment data
        db: Database session
        current_user: The authenticated user
        
    Returns:
        The updated Payment record
        
    Raises:
        HTTPException: 404 if payment not found
        HTTPException: 403 if user doesn't own the payment/subscription/payment method
    """
    db_obj = service.get_payment(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Payment not found")
    _ensure_payment_owner(db_obj, current_user)

    data = item_in.model_dump(exclude_unset=True)
    data.pop("user_id", None)

    if "subscription_id" in data and data["subscription_id"] is not None:
        subscription = subscription_service.get_subscription(db, id=data["subscription_id"])
        if subscription is None:
            raise HTTPException(status_code=404, detail="Subscription not found")
        _ensure_subscription_owner(subscription, current_user)

    if "payment_method_id" in data and data["payment_method_id"] is not None:
        payment_method = payment_method_service.get_payment_method(
            db,
            id=data["payment_method_id"],
        )
        if payment_method is None:
            raise HTTPException(status_code=404, detail="Payment method not found")
        _ensure_payment_method_owner(payment_method, current_user)

    return service.update_payment(db, db_obj=db_obj, obj_in=data)

@router.delete("/{id}", response_model=PaymentResponse)
def delete_payment(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Delete a payment record.
    
    Args:
        id: The UUID of the payment to delete
        db: Database session
        current_user: The authenticated user
        
    Returns:
        The deleted Payment record
        
    Raises:
        HTTPException: 404 if payment not found
        HTTPException: 403 if user doesn't own the payment
    """
    db_obj = service.get_payment(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Payment not found")
    _ensure_payment_owner(db_obj, current_user)
    return service.delete_payment(db, id=id)

@router.post("/{id}/refund", response_model=PaymentResponse)
def refund_payment(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Refund a specific payment.
    
    Args:
        id: The UUID of the payment to refund
        db: Database session
        current_user: The authenticated user
        
    Returns:
        The updated Payment record with REFUNDED status
        
    Raises:
        HTTPException: 404 if payment not found
        HTTPException: 403 if user doesn't own the payment
    """
    db_obj = service.get_payment(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Payment not found")
    _ensure_payment_owner(db_obj, current_user)
    
    service.handle_payment_reversal(db, payment_id=id)
    db.refresh(db_obj)
    return db_obj
