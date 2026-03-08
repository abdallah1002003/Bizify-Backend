# ruff: noqa
"""
Payment CRUD operations and payment processing.
"""
from __future__ import annotations

from datetime import timedelta
import logging
from decimal import Decimal
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Payment, PaymentMethod, Subscription, Usage
from app.models.enums import SubscriptionStatus, PaymentStatus
from app.services.billing import subscription_service
from app.services.base_service import BaseService
from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates
from app.core.exceptions import (
    ResourceNotFoundError,
    ValidationError,
    InvalidStateError,
    DatabaseError
)
from app.repositories.billing_repository import PaymentRepository, PaymentMethodRepository, SubscriptionRepository

logger = logging.getLogger(__name__)

_ALLOWED_PAYMENT_TRANSITIONS: dict[PaymentStatus, set[PaymentStatus]] = {
    PaymentStatus.PENDING: {PaymentStatus.COMPLETED, PaymentStatus.FAILED, PaymentStatus.REFUNDED},
    PaymentStatus.COMPLETED: {PaymentStatus.REFUNDED},
    PaymentStatus.FAILED: set(),
    PaymentStatus.REFUNDED: set(),
}


def _coerce_payment_status(raw: Any) -> PaymentStatus:
    if isinstance(raw, PaymentStatus):
        return raw
    try:
        return PaymentStatus(str(raw).lower())
    except ValueError as exc:
        raise ValidationError(
            message=f"Invalid payment status '{raw}'",
            field="status",
            details={"allowed": [s.value for s in PaymentStatus]},
        ) from exc


def _normalize_currency(raw: str | None) -> str:
    value = (raw or "usd").strip().upper()
    if len(value) != 3:
        raise ValidationError(
            message=f"Invalid currency '{raw}'",
            field="currency",
            details={"expected": "3-letter ISO code"},
        )
    return value

class PaymentService(BaseService):
    """Refactored class-based access to payments."""
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.payment_repo = PaymentRepository(db)
        self.method_repo = PaymentMethodRepository(db)
        self.sub_repo = SubscriptionRepository(db)
    async def get_payment(self, id: UUID) -> Optional[Payment]:
        return await self.payment_repo.get(id)

    async def get_payments(self, skip: int = 0, limit: int = 100, user_id: Optional[UUID] = None, status: Optional[PaymentStatus] = None) -> List[Payment]:
        return await self.payment_repo.get_all_filtered(skip=skip, limit=limit, user_id=user_id, status=status)

    async def create_payment(self, obj_in: Any) -> Payment:
        data = _to_update_dict(obj_in)
        if "amount" in data and data["amount"] is not None:
            try:
                amount = Decimal(str(data["amount"]))
            except Exception:
                raise ValidationError(message="Invalid amount format", field="amount")
        else:
            amount = Decimal("0")
            
        if amount <= 0:
            raise ValidationError(
                message=f"Payment amount must be positive, got {amount}",
                field="amount",
            )
        data["amount"] = amount
        data["currency"] = _normalize_currency(data.get("currency"))

        if "status" in data and data["status"] is not None:
            data["status"] = _coerce_payment_status(data["status"])

        subscription_id = data.get("subscription_id")
        user_id = data.get("user_id")
        if subscription_id is not None:
            subscription = await self.sub_repo.get(subscription_id)
            if subscription is None:
                raise ResourceNotFoundError(
                    resource_type="Subscription",
                    resource_id=str(subscription_id),
                    details={"operation": "create_payment"},
                )
            if user_id is not None and subscription.user_id != user_id:
                raise ValidationError(
                    message="Payment user_id does not match subscription owner",
                    details={
                        "subscription_user_id": str(subscription.user_id),
                        "payment_user_id": str(user_id),
                    },
                )

        payment_method_id = data.get("payment_method_id")
        if payment_method_id is not None:
            method = await self.method_repo.get(payment_method_id)
            if method is None:
                raise ResourceNotFoundError(
                    resource_type="PaymentMethod",
                    resource_id=str(payment_method_id),
                    details={"operation": "create_payment"},
                )
            if user_id is not None and method.user_id != user_id:
                raise ValidationError(
                    message="Payment method does not belong to payment user",
                    details={
                        "payment_method_user_id": str(method.user_id),
                        "payment_user_id": str(user_id),
                    },
                )

        return await self.payment_repo.create(data)

    async def update_payment(self, db_obj: Payment, obj_in: Any) -> Payment:
        update_data = _to_update_dict(obj_in)

        if "amount" in update_data and update_data["amount"] is not None:
            try:
                amount = Decimal(str(update_data["amount"]))
            except Exception:
                raise ValidationError(message="Invalid amount format", field="amount")
            if amount <= 0:
                raise ValidationError(
                    message=f"Payment amount must be positive, got {amount}",
                    field="amount",
                )
            update_data["amount"] = amount

        if "currency" in update_data and update_data["currency"] is not None:
            update_data["currency"] = _normalize_currency(update_data["currency"])

        if "status" in update_data and update_data["status"] is not None:
            new_status = _coerce_payment_status(update_data["status"])
            if new_status != db_obj.status:
                allowed = _ALLOWED_PAYMENT_TRANSITIONS.get(db_obj.status, set())
                if new_status not in allowed:
                    raise InvalidStateError(
                        message=f"Invalid payment status transition {db_obj.status.value} -> {new_status.value}",
                        current_state=db_obj.status.value,
                        required_state=" | ".join(sorted(s.value for s in allowed)) or "no transitions allowed",
                    )
            update_data["status"] = new_status

        return await self.payment_repo.update(db_obj, update_data)

    async def delete_payment(self, id: UUID) -> Optional[Payment]:
        return await self.payment_repo.delete(id)

    async def process_payment(self, subscription_id: UUID, amount: Decimal, method_id: UUID, currency: str = "usd") -> Payment:
        try:
            if amount <= 0:
                raise ValidationError(
                    message=f"Payment amount must be positive, got {amount}",
                    field="amount",
                    details={"provided_amount": amount}
                )
            
            subscription = await self.sub_repo.get(subscription_id)
            if subscription is None:
                raise ResourceNotFoundError(
                    resource_type="Subscription",
                    resource_id=str(subscription_id),
                    details={"operation": "process_payment"}
                )
            
            if subscription.status == SubscriptionStatus.CANCELED:
                raise InvalidStateError(
                    message=f"Cannot process payment for canceled subscription {subscription_id}",
                    current_state=str(subscription.status),
                    required_state="PENDING or ACTIVE",
                    details={"subscription_id": str(subscription_id)}
                )

            payment_method = await self.method_repo.get(method_id)
            if payment_method is None:
                raise ResourceNotFoundError(
                    resource_type="PaymentMethod",
                    resource_id=str(method_id),
                    details={"operation": "process_payment"},
                )
            if payment_method.user_id != subscription.user_id:
                raise ValidationError(
                    message="Payment method does not belong to subscription owner",
                    details={
                        "subscription_user_id": str(subscription.user_id),
                        "payment_method_user_id": str(payment_method.user_id),
                    },
                )

            db_payment = await self.payment_repo.create({
                "user_id": subscription.user_id,
                "subscription_id": subscription_id,
                "payment_method_id": method_id,
                "amount": amount,
                "currency": _normalize_currency(currency),
                "status": PaymentStatus.COMPLETED,
            }, auto_commit=False)

            subscription.status = SubscriptionStatus.ACTIVE
            base_end = subscription.end_date or _utc_now()
            subscription.end_date = base_end + timedelta(days=30)
            self.db.add(subscription)

            await self.db.commit()
            await self.db.refresh(db_payment)
            logger.info(f"Processed payment {db_payment.id} for subscription {subscription_id}: ${amount} {currency}")
            return db_payment
        except (ValidationError, ResourceNotFoundError, InvalidStateError):
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
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

    async def handle_payment_reversal(self, payment_id: UUID) -> None:
        try:
            payment = await self.payment_repo.get(payment_id)
            if payment is None:
                logger.warning(f"Payment {payment_id} not found for reversal")
                return

            payment.status = PaymentStatus.REFUNDED
            if payment.subscription_id is not None:
                subscription = await self.sub_repo.get(payment.subscription_id)
                if subscription is not None:
                    subscription.status = SubscriptionStatus.CANCELED
                    self.db.add(subscription)
                    
                    # Update usage limits to 0 asynchronously
                    from sqlalchemy import update
                    stmt = update(Usage).where(Usage.user_id == subscription.user_id).values(limit_value=0)
                    await self.db.execute(stmt)

            await self.db.commit()
            logger.info(f"Reversed payment {payment_id}")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error reversing payment {payment_id}: {e}")
            raise


def get_payment_service(db: AsyncSession) -> PaymentService:
    """Helper to return an instance of PaymentService."""
    return PaymentService(db)



# ----------------------------
# Payment
# ----------------------------

async def get_payment(db: AsyncSession, id: UUID) -> Optional[Payment]:
    """Retrieve a single payment by its unique ID.
    
    Args:
        db: Database session
        id: The payment UUID to retrieve
        
    Returns:
        The Payment object if found, None otherwise
    """
    return await db.get(Payment, id)


async def get_payments(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
    status: Optional[PaymentStatus] = None,
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
    stmt = select(Payment)
    if user_id is not None:
        stmt = stmt.where(Payment.user_id == user_id)
    if status is not None:
        stmt = stmt.where(Payment.status == status)
    stmt = (
        stmt.order_by(Payment.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_payment(db: AsyncSession, obj_in: Any) -> Payment:
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
        data = _to_update_dict(obj_in)
        if "amount" in data and data["amount"] is not None:
            try:
                amount = Decimal(str(data["amount"]))
            except Exception:
                raise ValidationError(message="Invalid amount format", field="amount")
        else:
            amount = Decimal("0")
            
        if amount <= 0:
            raise ValidationError(
                message=f"Payment amount must be positive, got {amount}",
                field="amount",
            )
        data["amount"] = amount
        data["currency"] = _normalize_currency(data.get("currency"))

        if "status" in data and data["status"] is not None:
            data["status"] = _coerce_payment_status(data["status"])

        subscription_id = data.get("subscription_id")
        user_id = data.get("user_id")
        if subscription_id is not None:
            subscription = await db.get(Subscription, subscription_id)
            if subscription is None:
                raise ResourceNotFoundError(
                    resource_type="Subscription",
                    resource_id=str(subscription_id),
                    details={"operation": "create_payment"},
                )
            if user_id is not None and subscription.user_id != user_id:
                raise ValidationError(
                    message="Payment user_id does not match subscription owner",
                    details={
                        "subscription_user_id": str(subscription.user_id),
                        "payment_user_id": str(user_id),
                    },
                )

        payment_method_id = data.get("payment_method_id")
        if payment_method_id is not None:
            method = await db.get(PaymentMethod, payment_method_id)
            if method is None:
                raise ResourceNotFoundError(
                    resource_type="PaymentMethod",
                    resource_id=str(payment_method_id),
                    details={"operation": "create_payment"},
                )
            if user_id is not None and method.user_id != user_id:
                raise ValidationError(
                    message="Payment method does not belong to payment user",
                    details={
                        "payment_method_user_id": str(method.user_id),
                        "payment_user_id": str(user_id),
                    },
                )

        db_obj = Payment(**data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        logger.info(f"Created payment {db_obj.id}")
        return db_obj
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating payment: {e}")
        raise


async def update_payment(db: AsyncSession, db_obj: Payment, obj_in: Any) -> Payment:
    """Update mutable fields on a payment."""

    update_data = _to_update_dict(obj_in)

    if "amount" in update_data and update_data["amount"] is not None:
        try:
            amount = Decimal(str(update_data["amount"]))
        except Exception:
            raise ValidationError(message="Invalid amount format", field="amount")
        if amount <= 0:
            raise ValidationError(
                message=f"Payment amount must be positive, got {amount}",
                field="amount",
            )
        update_data["amount"] = amount

    if "currency" in update_data and update_data["currency"] is not None:
        update_data["currency"] = _normalize_currency(update_data["currency"])

    if "status" in update_data and update_data["status"] is not None:
        new_status = _coerce_payment_status(update_data["status"])
        if new_status != db_obj.status:
            allowed = _ALLOWED_PAYMENT_TRANSITIONS.get(db_obj.status, set())
            if new_status not in allowed:
                raise InvalidStateError(
                    message=f"Invalid payment status transition {db_obj.status.value} -> {new_status.value}",
                    current_state=db_obj.status.value,
                    required_state=" | ".join(sorted(s.value for s in allowed)) or "no transitions allowed",
                )
        update_data["status"] = new_status

    _apply_updates(db_obj, update_data)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete_payment(db: AsyncSession, id: UUID) -> Optional[Payment]:
    """Delete a payment by id."""

    # First check if it exists
    db_obj = await get_payment(db, id=id)
    if not db_obj:
        logger.debug(f"Payment {id} not found for deletion")
        return None

    logger.debug(f"Deleting payment {id}")
    # Keep a copy of the ID before deletion
    payment_id_copy = UUID(str(db_obj.id))  # Make a copy of the UUID
    
    # Mark for deletion and commit
    await db.delete(db_obj)
    await db.commit()
    
    # Create a new detached Payment instance to avoid lazy loading issues
    deleted_payment = Payment(id=payment_id_copy)
    return deleted_payment


async def process_payment(
    db: AsyncSession,
    subscription_id: UUID,
    amount: Decimal,
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
        subscription = await subscription_service.get_subscription(db, id=subscription_id)
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

        payment_method = await db.get(PaymentMethod, method_id)
        if payment_method is None:
            raise ResourceNotFoundError(
                resource_type="PaymentMethod",
                resource_id=str(method_id),
                details={"operation": "process_payment"},
            )
        if payment_method.user_id != subscription.user_id:
            raise ValidationError(
                message="Payment method does not belong to subscription owner",
                details={
                    "subscription_user_id": str(subscription.user_id),
                    "payment_method_user_id": str(payment_method.user_id),
                },
            )

        db_payment = Payment(
            user_id=subscription.user_id,
            subscription_id=subscription_id,
            payment_method_id=method_id,
            amount=amount,
            currency=_normalize_currency(currency),
            status=PaymentStatus.COMPLETED,
        )
        db.add(db_payment)

        subscription.status = SubscriptionStatus.ACTIVE
        base_end = subscription.end_date or _utc_now()
        subscription.end_date = base_end + timedelta(days=30)

        await db.commit()
        await db.refresh(db_payment)
        logger.info(f"Processed payment {db_payment.id} for subscription {subscription_id}: ${amount} {currency}")
        return db_payment
    except (ValidationError, ResourceNotFoundError, InvalidStateError):
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
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


async def process_subscription_payment(db: AsyncSession, subscription_id: UUID, amount: Decimal, payment_method_id: UUID):
    """Backward-compatible wrapper around `process_payment`."""
    return await process_payment(
        db,
        subscription_id=subscription_id,
        amount=amount,
        method_id=payment_method_id,
    )


async def handle_payment_reversal(db: AsyncSession, payment_id: UUID) -> None:
    """Reverse a payment and cancel the linked subscription if present.
    
    This function:
    1. Marks the payment as REFUNDED
    2. Cancels the related subscription (if exists)
    3. Sets usage limits to 0 for the user
    
    Args:
        db: Database session
        payment_id: UUID of the payment to reverse
    """
    try:
        payment = await get_payment(db, id=payment_id)
        if payment is None:
            logger.warning(f"Payment {payment_id} not found for reversal")
            return

        payment.status = PaymentStatus.REFUNDED
        if payment.subscription_id is not None:
            subscription = await subscription_service.get_subscription(db, id=payment.subscription_id)
            if subscription is not None:
                subscription.status = SubscriptionStatus.CANCELED
                # Update usage limits to 0 asynchronously
                from sqlalchemy import update
                stmt = update(Usage).where(Usage.user_id == subscription.user_id).values(limit_value=0)
                await db.execute(stmt)

        await db.commit()
        logger.info(f"Reversed payment {payment_id}")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error reversing payment {payment_id}: {e}")
        raise
