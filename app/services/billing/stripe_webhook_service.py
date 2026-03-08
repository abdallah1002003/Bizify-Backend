from __future__ import annotations

import logging
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import PaymentStatus, SubscriptionStatus
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class StripeWebhookService(BaseService):
    """Refactored class-based access to Stripe webhook handlers."""
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        from app.repositories.billing_repository import (
            PaymentRepository, SubscriptionRepository,
            StripeWebhookRepository
        )
        from app.repositories.user_repository import UserRepository
        
        self.payment_repo = PaymentRepository(db)
        self.sub_repo = SubscriptionRepository(db)
        self.user_repo = UserRepository(db)
        self.event_repo = StripeWebhookRepository(db)
        self.repo = self.event_repo

    async def dispatch(self, event: Dict[str, Any]) -> bool:
        """
        Route a verified Stripe event to its handler.
        Includes idempotency checks to prevent duplicate processing.
        """
        event_type: str = event.get("type", "")
        event_id: str = event.get("id", "")
        data = event.get("data", {}).get("object", {})

        handler_map = {
            "payment_intent.succeeded": self.handle_payment_intent_succeeded,
            "payment_intent.payment_failed": self.handle_payment_intent_failed,
            "customer.subscription.deleted": self.handle_subscription_deleted,
            "customer.subscription.updated": self.handle_subscription_updated,
            "invoice.payment_succeeded": self.handle_invoice_payment_succeeded,
            "checkout.session.completed": self.handle_checkout_session_completed,
        }

        handler = handler_map.get(event_type)
        if handler is None:
            logger.debug("Stripe: unhandled event type '%s' — ignoring", event_type)
            return False

        if event_id:
            # Idempotency check
            existing = await self.event_repo.get(event_id)
            if existing:
                logger.info("Stripe event %s already processed. Ignoring duplicate.", event_id)
                return True

            # Reserve the event ID
            try:
                await self.event_repo.create({"id": event_id, "event_id": event_id, "source": "stripe"})
            except Exception:
                logger.info("Stripe event %s already processed (caught via constraint). Ignoring duplicate.", event_id)
                return True

        try:
            await handler(data)
            await self.event_repo.commit()
            return True
        except Exception:
            await self.event_repo.rollback()
            logger.exception("Error handling Stripe event '%s'", event_type)
            raise

    async def handle_event(self, event: Any) -> bool:
        """Alias for dispatch, expected by some tests."""
        return await self.dispatch(event)

    async def handle_payment_intent_succeeded(self, data: Dict[str, Any]) -> None:
        """payment_intent.succeeded → mark matching Payment as COMPLETED."""
        intent_id = data.get("id", "")
        payment = await self.payment_repo.get_pending_by_payment_intent(intent_id)
        if payment:
            await self.payment_repo.update(payment, {"status": PaymentStatus.COMPLETED}, auto_commit=False)
            logger.info("Payment %s marked COMPLETED", payment.id)

    async def handle_payment_intent_failed(self, data: Dict[str, Any]) -> None:
        """payment_intent.payment_failed → mark matching Payment as FAILED."""
        intent_id = data.get("id", "")
        payment = await self.payment_repo.get_pending_by_payment_intent(intent_id)
        if payment:
            await self.payment_repo.update(payment, {"status": PaymentStatus.FAILED}, auto_commit=False)
            logger.info("Payment %s marked FAILED", payment.id)

    async def handle_subscription_deleted(self, data: Dict[str, Any]) -> None:
        """customer.subscription.deleted → cancel matching Subscription."""
        stripe_sub_id = data.get("id", "")
        sub = await self.sub_repo.get_by_stripe_id(stripe_sub_id)
        if sub:
            await self.sub_repo.update(sub, {"status": SubscriptionStatus.CANCELED}, auto_commit=False)
            logger.info("Subscription %s cancelled", sub.id)

    async def handle_subscription_updated(self, data: Dict[str, Any]) -> None:
        """customer.subscription.updated → sync status / end_date."""
        stripe_sub_id = data.get("id", "")
        sub = await self.sub_repo.get_by_stripe_id(stripe_sub_id)
        if not sub:
            return

        update_data: Dict[str, Any] = {}
        stripe_status = data.get("status", "")
        status_map = {
            "active": SubscriptionStatus.ACTIVE,
            "canceled": SubscriptionStatus.CANCELED,
            "past_due": SubscriptionStatus.EXPIRED,
            "unpaid": SubscriptionStatus.EXPIRED,
        }
        new_status = status_map.get(stripe_status)
        if new_status:
            update_data["status"] = new_status

        current_period_end = data.get("current_period_end")
        if current_period_end:
            from datetime import datetime, timezone
            # current_period_end is a Unix timestamp; convert to datetime
            end_date = datetime.fromtimestamp(current_period_end, tz=timezone.utc)
            update_data["end_date"] = end_date

        if update_data:
            await self.sub_repo.update(sub, update_data, auto_commit=False)
            logger.info("Subscription %s updated", sub.id)

    async def handle_invoice_payment_succeeded(self, data: Dict[str, Any]) -> None:
        """invoice.payment_succeeded handler."""
        customer_id = data.get("customer", "")
        if customer_id:
            user = await self.user_repo.get_by_stripe_customer_id(customer_id)
            if user:
                logger.info("Invoice for customer %s matched user %s", customer_id, user.id)

    async def handle_checkout_session_completed(self, data: Dict[str, Any]) -> None:
        """checkout.session.completed → create a Subscription record."""
        subscription_id = data.get("subscription", "")
        metadata = data.get("metadata", {})
        user_id = metadata.get("user_id")
        plan_id = metadata.get("plan_id")

        if not user_id or not plan_id:
            return

        if subscription_id:
            existing = await self.sub_repo.get_by_stripe_id(subscription_id)
            if existing:
                return

        status_str = data.get("payment_status", "")
        status = SubscriptionStatus.ACTIVE if status_str == "paid" else SubscriptionStatus.PENDING

        from datetime import datetime, timezone
        await self.sub_repo.create({
            "user_id": user_id,
            "plan_id": plan_id,
            "status": status,
            "stripe_subscription_id": subscription_id,
            "start_date": datetime.now(timezone.utc),
        }, auto_commit=False)
        logger.info("Created local Subscription for user %s", user_id)
