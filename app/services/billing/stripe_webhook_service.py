from __future__ import annotations

import logging
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Payment, Subscription
from app.models.enums import PaymentStatus, SubscriptionStatus
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class StripeWebhookService(BaseService):
    """Service for handling Stripe webhook events and dispatching them to handlers."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        from app.repositories.billing_repository import PaymentRepository, SubscriptionRepository, ProcessedEventRepository
        from app.repositories.user_repository import UserRepository
        self.payment_repo = PaymentRepository(db)
        self.sub_repo = SubscriptionRepository(db)
        self.user_repo = UserRepository(db)
        self.event_repo = ProcessedEventRepository(db)

    # ---------------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------------

    async def _find_payment_by_stripe_ref(self, stripe_payment_intent_id: str) -> Payment | None:
        return await self.payment_repo.get_pending_by_payment_intent(stripe_payment_intent_id)

    async def _find_subscription_by_stripe_id(self, stripe_sub_id: str) -> Subscription | None:
        return await self.sub_repo.get_by_stripe_id(stripe_sub_id)

    async def _find_user_by_stripe_customer_id(self, stripe_customer_id: str):
        return await self.user_repo.get_by_stripe_customer_id(stripe_customer_id)

    # ---------------------------------------------------------------------------
    # Event handlers
    # ---------------------------------------------------------------------------

    async def handle_payment_intent_succeeded(self, data: Dict[str, Any]) -> None:
        intent_id = data.get("id", "")
        logger.info("Stripe: payment_intent.succeeded — intent=%s", intent_id)
        payment = await self._find_payment_by_stripe_ref(intent_id)
        if payment is None:
            logger.warning("No local Payment found for intent %s — skipping", intent_id)
            return
        await self.payment_repo.update(payment, {"status": PaymentStatus.COMPLETED})
        logger.info("Payment %s marked COMPLETED", payment.id)

    async def handle_payment_intent_failed(self, data: Dict[str, Any]) -> None:
        intent_id = data.get("id", "")
        logger.info("Stripe: payment_intent.payment_failed — intent=%s", intent_id)
        payment = await self._find_payment_by_stripe_ref(intent_id)
        if payment is None:
            logger.warning("No local Payment found for intent %s — skipping", intent_id)
            return
        await self.payment_repo.update(payment, {"status": PaymentStatus.FAILED})
        logger.info("Payment %s marked FAILED", payment.id)

    async def handle_subscription_deleted(self, data: Dict[str, Any]) -> None:
        stripe_sub_id = data.get("id", "")
        logger.info("Stripe: customer.subscription.deleted — sub=%s", stripe_sub_id)
        sub = await self._find_subscription_by_stripe_id(stripe_sub_id)
        if sub is None:
            logger.warning("No local Subscription found for Stripe sub %s — skipping", stripe_sub_id)
            return
        await self.sub_repo.update(sub, {"status": SubscriptionStatus.CANCELED})
        logger.info("Subscription %s cancelled", sub.id)

    async def handle_subscription_updated(self, data: Dict[str, Any]) -> None:
        stripe_sub_id = data.get("id", "")
        logger.info("Stripe: customer.subscription.updated — sub=%s", stripe_sub_id)
        sub = await self._find_subscription_by_stripe_id(stripe_sub_id)
        if sub is None:
            logger.warning("No local Subscription found for Stripe sub %s — skipping", stripe_sub_id)
            return
        stripe_status = data.get("status", "")
        status_map = {
            "active": SubscriptionStatus.ACTIVE,
            "canceled": SubscriptionStatus.CANCELED,
            "past_due": SubscriptionStatus.EXPIRED,
            "unpaid": SubscriptionStatus.EXPIRED,
        }
        new_status = status_map.get(stripe_status)
        update_data: dict[str, Any] = {}
        if new_status:
            update_data["status"] = new_status
        current_period_end = data.get("current_period_end")
        if current_period_end:
            from datetime import datetime, timezone
            update_data["end_date"] = datetime.fromtimestamp(current_period_end, tz=timezone.utc)
        if update_data:
            await self.sub_repo.update(sub, update_data)
        logger.info("Subscription %s updated — status=%s", sub.id, stripe_status)

    async def handle_invoice_payment_succeeded(self, data: Dict[str, Any]) -> None:
        invoice_id = data.get("id", "")
        amount_paid = data.get("amount_paid", 0)
        currency = (data.get("currency") or "usd").upper()
        customer_id = data.get("customer", "")
        logger.info("Stripe: invoice.payment_succeeded — invoice=%s amount=%s %s customer=%s", invoice_id, amount_paid, currency, customer_id)
        user = await self._find_user_by_stripe_customer_id(customer_id) if customer_id else None
        if user:
            logger.info("Invoice %s linked to user %s (amount: %s %s)", invoice_id, user.id, amount_paid / 100, currency)
        else:
            logger.info("Invoice %s recorded (amount: %s %s) — no local user matched", invoice_id, amount_paid / 100, currency)

    async def handle_checkout_session_completed(self, data: Dict[str, Any]) -> None:
        session_id = data.get("id", "")
        subscription_id = data.get("subscription", "")
        metadata = data.get("metadata", {})
        user_id = metadata.get("user_id")
        plan_id = metadata.get("plan_id")
        logger.info("Stripe: checkout.session.completed — session=%s, user=%s, plan=%s", session_id, user_id, plan_id)
        if not user_id or not plan_id:
            logger.warning("Session %s missing user_id or plan_id in metadata, cannot create Subscription", session_id)
            return
        if subscription_id:
            existing = await self._find_subscription_by_stripe_id(subscription_id)
            if existing:
                logger.info("Local Subscription already exists for Stripe sub %s", subscription_id)
                return
        from app.models.enums import SubscriptionStatus
        from datetime import datetime, timezone
        status_str = data.get("payment_status", "")
        status = SubscriptionStatus.ACTIVE if status_str == "paid" else SubscriptionStatus.PENDING
        new_sub = await self.sub_repo.create({
            "user_id": user_id,
            "plan_id": plan_id,
            "status": status,
            "stripe_subscription_id": subscription_id,
            "start_date": datetime.now(timezone.utc),
        })
        logger.info("Created local Subscription %s for user %s and plan %s", new_sub.id, user_id, plan_id)

    # ---------------------------------------------------------------------------
    # Dispatcher
    # ---------------------------------------------------------------------------

    async def dispatch(self, event: Any) -> bool:
        """Route a verified Stripe event to its handler with idempotency checks."""
        _HANDLERS = {
            "payment_intent.succeeded": self.handle_payment_intent_succeeded,
            "payment_intent.payment_failed": self.handle_payment_intent_failed,
            "customer.subscription.deleted": self.handle_subscription_deleted,
            "customer.subscription.updated": self.handle_subscription_updated,
            "invoice.payment_succeeded": self.handle_invoice_payment_succeeded,
            "checkout.session.completed": self.handle_checkout_session_completed,
        }
        event_type: str = event.get("type", "")
        event_id: str = event.get("id", "")
        data = event.get("data", {}).get("object", {})

        handler = _HANDLERS.get(event_type)
        if handler is None:
            logger.debug("Stripe: unhandled event type '%s' — ignoring", event_type)
            return False

        if not event_id:
            logger.warning("Stripe event missing 'id'. Proceeding without idempotency check.")
        else:
            existing = await self.event_repo.get_by_event_id(event_id, "stripe")
            if existing:
                logger.info("Stripe event %s already processed. Ignoring duplicate.", event_id)
                return True
            # Use create_safe() to handle race conditions where concurrent requests
            # insert the same event_id between the check and create above
            created = await self.event_repo.create_safe(
                {"event_id": event_id, "source": "stripe"}, 
                auto_commit=False
            )
            if created is None:
                # Another transaction inserted this event_id concurrently
                logger.info("Stripe event %s already processed (caught via constraint). Ignoring duplicate.", event_id)
                return True

        try:
            await handler(data)
            await self.event_repo.commit()
        except Exception:
            await self.event_repo.rollback()
            logger.exception("Error handling Stripe event '%s'", event_type)
            raise

        return True


