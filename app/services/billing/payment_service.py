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
from app.repositories.billing_repository import PaymentRepository, UsageRepository, SubscriptionRepository, PaymentMethodRepository
from app.services.billing import subscription_service
from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates
from app.core.exceptions import (
    ResourceNotFoundError,
    ValidationError,
    InvalidStateError,
    DatabaseError
)
from app.services.base_service import BaseService

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
    """Service for managing Payments and payment processing workflows."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self.payment_repo = PaymentRepository(db)
        self.usage_repo = UsageRepository(db)
        self.sub_repo = SubscriptionRepository(db)
        self.payment_method_repo = PaymentMethodRepository(db)

    async def get_payment(self, id: UUID) -> Optional[Payment]:
        """Retrieve a single payment by ID."""
        return await self.payment_repo.get(id)

    async def get_payments(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[UUID] = None,
        status: Optional[PaymentStatus] = None,
    ) -> List[Payment]:
        """Retrieve payments with pagination and optional filtering."""
        return await self.payment_repo.get_all_filtered(skip=skip, limit=limit, user_id=user_id, status=status)

    async def create_payment(self, obj_in: Any) -> Payment:
        """Create a new payment record with validation."""
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
                method = await self.payment_method_repo.get(payment_method_id)
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

            db_obj = await self.payment_repo.create(data)
            logger.info(f"Created payment {db_obj.id}")
            return db_obj
        except Exception as e:
            await self.payment_repo.rollback()
            logger.error(f"Error creating payment: {e}")
            raise

    async def update_payment(self, db_obj: Payment, obj_in: Any) -> Payment:
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

        return await self.payment_repo.update(db_obj, update_data)

    async def delete_payment(self, id: UUID) -> Optional[Payment]:
        """Delete a payment by id."""
        db_obj = await self.get_payment(id)
        if not db_obj:
            logger.debug(f"Payment {id} not found for deletion")
            return None

        logger.debug(f"Deleting payment {id}")
        return await self.payment_repo.delete(db_obj)

    async def process_payment(
        self,
        subscription_id: UUID,
        amount: Decimal,
        method_id: UUID,
        currency: str = "usd",
    ) -> Payment:
        """Create a successful payment and activate the related subscription."""
        try:
            if amount <= 0:
                raise ValidationError(
                    message=f"Payment amount must be positive, got {amount}",
                    field="amount",
                    details={"provided_amount": amount}
                )

            subscription = await subscription_service.SubscriptionService(self.db).get_subscription(id=subscription_id)
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

            payment_method = await self.payment_method_repo.get(method_id)
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
            })

            now = _utc_now()
            base_end = subscription.end_date if subscription.end_date and subscription.end_date > now else now
            await self.sub_repo.update(subscription, {
                "status": SubscriptionStatus.ACTIVE,
                "end_date": base_end + timedelta(days=30)
            })
            logger.info(f"Processed payment {db_payment.id} for subscription {subscription_id}: ${amount} {currency}")
            return db_payment
        except (ValidationError, ResourceNotFoundError, InvalidStateError):
            await self.payment_repo.rollback()
            raise
        except Exception as e:
            await self.payment_repo.rollback()
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

    async def process_subscription_payment(
        self,
        subscription_id: UUID,
        amount: Decimal,
        payment_method_id: UUID,
    ) -> Payment:
        """Backward-compatible wrapper around process_payment."""
        return await self.process_payment(
            subscription_id=subscription_id,
            amount=amount,
            method_id=payment_method_id,
        )

    async def handle_payment_reversal(self, payment_id: UUID) -> None:
        """Reverse a payment and cancel the linked subscription if present."""
        try:
            payment = await self.get_payment(payment_id)
            if payment is None:
                logger.warning(f"Payment {payment_id} not found for reversal")
                return

            await self.payment_repo.update(payment, {"status": PaymentStatus.REFUNDED})
            if payment.subscription_id is not None:
                subscription = await subscription_service.SubscriptionService(self.db).get_subscription(id=payment.subscription_id)
                if subscription is not None:
                    await self.sub_repo.update(subscription, {"status": SubscriptionStatus.CANCELED})
                    
                    usages = await self.usage_repo.get_for_user(subscription.user_id)
                    for usage in usages:
                        await self.usage_repo.update(usage, {"limit_value": 0})

            logger.info(f"Reversed payment {payment_id}")
        except Exception as e:
            await self.payment_repo.rollback()
            logger.error(f"Error reversing payment {payment_id}: {e}")
            raise


async def get_payment_service(db: AsyncSession) -> PaymentService:
    """Dependency provider for PaymentService."""
    return PaymentService(db)



