from __future__ import annotations

import logging
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Payment, Subscription
from app.models.enums import PaymentStatus, SubscriptionStatus

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _find_payment_by_stripe_ref(db: AsyncSession, stripe_payment_intent_id: str) -> Payment | None:
    """Look up a Payment whose associated PaymentMethod token_ref equals the Stripe PaymentIntent ID."""
    from app.models import PaymentMethod
    stmt = (
        select(Payment)
        .join(PaymentMethod)
        .where(PaymentMethod.token_ref == stripe_payment_intent_id)
        .where(Payment.status == PaymentStatus.PENDING)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _find_subscription_by_stripe_id(db: AsyncSession, stripe_sub_id: str) -> Subscription | None:
    """Look up a local Subscription by its Stripe subscription ID."""
    stmt = select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _find_user_by_stripe_customer_id(db: AsyncSession, stripe_customer_id: str):
    """Look up a local User by their Stripe customer ID."""
    from app.models import User
    stmt = select(User).where(User.stripe_customer_id == stripe_customer_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------

async def handle_payment_intent_succeeded(db: AsyncSession, data: Dict[str, Any]) -> None:
    """payment_intent.succeeded → mark matching Payment as COMPLETED."""
    intent_id = data.get("id", "")
    logger.info("Stripe: payment_intent.succeeded — intent=%s", intent_id)

    payment = await _find_payment_by_stripe_ref(db, intent_id)
    if payment is None:
        logger.warning("No local Payment found for intent %s — skipping", intent_id)
        return

    payment.status = PaymentStatus.COMPLETED
    await db.commit()
    logger.info("Payment %s marked COMPLETED", payment.id)


async def handle_payment_intent_failed(db: AsyncSession, data: Dict[str, Any]) -> None:
    """payment_intent.payment_failed → mark matching Payment as FAILED."""
    intent_id = data.get("id", "")
    logger.info("Stripe: payment_intent.payment_failed — intent=%s", intent_id)

    payment = await _find_payment_by_stripe_ref(db, intent_id)
    if payment is None:
        logger.warning("No local Payment found for intent %s — skipping", intent_id)
        return

    payment.status = PaymentStatus.FAILED
    await db.commit()
    logger.info("Payment %s marked FAILED", payment.id)


async def handle_subscription_deleted(db: AsyncSession, data: Dict[str, Any]) -> None:
    """customer.subscription.deleted → cancel matching Subscription."""
    stripe_sub_id = data.get("id", "")
    logger.info("Stripe: customer.subscription.deleted — sub=%s", stripe_sub_id)

    sub = await _find_subscription_by_stripe_id(db, stripe_sub_id)
    if sub is None:
        logger.warning("No local Subscription found for Stripe sub %s — skipping", stripe_sub_id)
        return

    sub.status = SubscriptionStatus.CANCELED
    await db.commit()
    logger.info("Subscription %s cancelled", sub.id)


async def handle_subscription_updated(db: AsyncSession, data: Dict[str, Any]) -> None:
    """customer.subscription.updated → sync status / end_date."""
    stripe_sub_id = data.get("id", "")
    logger.info("Stripe: customer.subscription.updated — sub=%s", stripe_sub_id)

    sub = await _find_subscription_by_stripe_id(db, stripe_sub_id)
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
    if new_status:
        sub.status = new_status

    current_period_end = data.get("current_period_end")
    if current_period_end:
        from datetime import datetime, timezone
        sub.end_date = datetime.fromtimestamp(current_period_end, tz=timezone.utc)

    await db.commit()
    logger.info("Subscription %s updated — status=%s", sub.id, stripe_status)


async def handle_invoice_payment_succeeded(db: AsyncSession, data: Dict[str, Any]) -> None:
    """invoice.payment_succeeded → log a COMPLETED Payment row if not already present."""
    invoice_id = data.get("id", "")
    amount_paid = data.get("amount_paid", 0)
    currency = (data.get("currency") or "usd").upper()
    customer_id = data.get("customer", "")

    logger.info(
        "Stripe: invoice.payment_succeeded — invoice=%s amount=%s %s customer=%s",
        invoice_id, amount_paid, currency, customer_id,
    )

    user = await _find_user_by_stripe_customer_id(db, customer_id) if customer_id else None
    if user:
        logger.info("Invoice %s linked to user %s (amount: %s %s)", invoice_id, user.id, amount_paid / 100, currency)
    else:
        logger.info("Invoice %s recorded (amount: %s %s) — no local user matched", invoice_id, amount_paid / 100, currency)


async def handle_checkout_session_completed(db: AsyncSession, data: Dict[str, Any]) -> None:
    """checkout.session.completed → create a Subscription record in the database."""
    session_id = data.get("id", "")
    subscription_id = data.get("subscription", "")
    metadata = data.get("metadata", {})
    user_id = metadata.get("user_id")
    plan_id = metadata.get("plan_id")

    logger.info("Stripe: checkout.session.completed — session=%s, user=%s, plan=%s", session_id, user_id, plan_id)

    if not user_id or not plan_id:
        logger.warning("Session %s missing user_id or plan_id in metadata, cannot create Subscription", session_id)
        return

    # Check if a subscription already exists for this stripe sub ID to prevent duplicates
    if subscription_id:
        existing = await _find_subscription_by_stripe_id(db, subscription_id)
        if existing:
            logger.info("Local Subscription already exists for Stripe sub %s", subscription_id)
            return

    from app.models.billing.billing import Subscription
    from app.models.enums import SubscriptionStatus
    from datetime import datetime, timezone
    
    # Normally Stripe active means the payment succeeded.
    status_str = data.get("payment_status", "")
    if status_str == "paid":
        status = SubscriptionStatus.ACTIVE
    else:
        status = SubscriptionStatus.PENDING

    # Create the local Subscription record
    new_sub = Subscription(
        user_id=user_id,
        plan_id=plan_id,
        status=status,
        stripe_subscription_id=subscription_id,
        start_date=datetime.now(timezone.utc),
    )
    db.add(new_sub)
    await db.commit()
    logger.info("Created local Subscription %s for user %s and plan %s", new_sub.id, user_id, plan_id)


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

_HANDLERS = {
    "payment_intent.succeeded": handle_payment_intent_succeeded,
    "payment_intent.payment_failed": handle_payment_intent_failed,
    "customer.subscription.deleted": handle_subscription_deleted,
    "customer.subscription.updated": handle_subscription_updated,
    "invoice.payment_succeeded": handle_invoice_payment_succeeded,
    "checkout.session.completed": handle_checkout_session_completed,
}


async def dispatch(db: AsyncSession, event: Any) -> bool:
    """
    Route a verified Stripe event to its handler.
    Includes idempotency checks to prevent duplicate processing.

    Returns True if a handler was found or if the event was already processed,
    False if the event type is unknown (which is not an error — forward-compatible by design).
    """
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
        from app.models.billing.processed_event import ProcessedEvent
        from sqlalchemy.exc import IntegrityError
        
        # Check if already processed (Read-before-write optimization)
        stmt = select(ProcessedEvent).where(ProcessedEvent.event_id == event_id, ProcessedEvent.source == "stripe")
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            logger.info("Stripe event %s already processed. Ignoring duplicate.", event_id)
            return True

        # Try to reserve the event ID
        try:
            async with db.begin_nested(): # Savepoint for SQLite/Postgres
                processed_event_record = ProcessedEvent(event_id=event_id, source="stripe")
                db.add(processed_event_record)
                await db.flush()
        except IntegrityError:
            # Note: begin_nested already rolled back on exception
            logger.info("Stripe event %s already processed (caught via constraint). Ignoring duplicate.", event_id)
            return True
        except Exception as e:
            logger.error("Failed to record idempotency key for event %s: %s", event_id, e)
            raise

    try:
        await handler(db, data)
        await db.commit() # Commit the handler changes and the ProcessedEvent record
    except Exception:
        await db.rollback() # Rollback everything, including the ProcessedEvent record
        logger.exception("Error handling Stripe event '%s'", event_type)
        raise  # re-raise so the route can return 500 and Stripe will retry

    return True
