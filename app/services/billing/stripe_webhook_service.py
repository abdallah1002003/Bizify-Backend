"""
Stripe Webhook Service — pure business logic, no FastAPI imports.

Handles five Stripe event types and maps them onto the local DB models
(Payment, Subscription). All functions follow the same signature:

    handler(db: Session, event_data: dict) -> None

Use ``dispatch(db, event)`` as the single entry point from the route.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.models import Payment, Subscription
from app.models.enums import PaymentStatus, SubscriptionStatus

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _find_payment_by_stripe_ref(db: Session, stripe_payment_intent_id: str) -> Payment | None:
    """Look up a Payment whose associated PaymentMethod token_ref equals the Stripe PaymentIntent ID."""
    return (
        db.query(Payment)
        .join(Payment.payment_method)
        .filter_by(token_ref=stripe_payment_intent_id)
        .filter(Payment.status == PaymentStatus.PENDING)
        .first()
    )


def _find_subscription_by_stripe_id(db: Session, stripe_sub_id: str) -> Subscription | None:
    """Look up a local Subscription by its Stripe subscription ID."""
    return (
        db.query(Subscription)
        .filter(Subscription.stripe_subscription_id == stripe_sub_id)
        .first()
    )


def _find_user_by_stripe_customer_id(db: Session, stripe_customer_id: str):
    """Look up a local User by their Stripe customer ID."""
    from app.models import User
    return db.query(User).filter(User.stripe_customer_id == stripe_customer_id).first()


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------

def handle_payment_intent_succeeded(db: Session, data: Dict[str, Any]) -> None:
    """payment_intent.succeeded → mark matching Payment as COMPLETED."""
    intent_id = data.get("id", "")
    logger.info("Stripe: payment_intent.succeeded — intent=%s", intent_id)

    payment = _find_payment_by_stripe_ref(db, intent_id)
    if payment is None:
        logger.warning("No local Payment found for intent %s — skipping", intent_id)
        return

    payment.status = PaymentStatus.COMPLETED
    db.commit()
    logger.info("Payment %s marked COMPLETED", payment.id)


def handle_payment_intent_failed(db: Session, data: Dict[str, Any]) -> None:
    """payment_intent.payment_failed → mark matching Payment as FAILED."""
    intent_id = data.get("id", "")
    logger.info("Stripe: payment_intent.payment_failed — intent=%s", intent_id)

    payment = _find_payment_by_stripe_ref(db, intent_id)
    if payment is None:
        logger.warning("No local Payment found for intent %s — skipping", intent_id)
        return

    payment.status = PaymentStatus.FAILED
    db.commit()
    logger.info("Payment %s marked FAILED", payment.id)


def handle_subscription_deleted(db: Session, data: Dict[str, Any]) -> None:
    """customer.subscription.deleted → cancel matching Subscription."""
    stripe_sub_id = data.get("id", "")
    logger.info("Stripe: customer.subscription.deleted — sub=%s", stripe_sub_id)

    sub = _find_subscription_by_stripe_id(db, stripe_sub_id)
    if sub is None:
        logger.warning("No local Subscription found for Stripe sub %s — skipping", stripe_sub_id)
        return

    sub.status = SubscriptionStatus.CANCELLED
    db.commit()
    logger.info("Subscription %s cancelled", sub.id)


def handle_subscription_updated(db: Session, data: Dict[str, Any]) -> None:
    """customer.subscription.updated → sync status / end_date."""
    stripe_sub_id = data.get("id", "")
    logger.info("Stripe: customer.subscription.updated — sub=%s", stripe_sub_id)

    sub = _find_subscription_by_stripe_id(db, stripe_sub_id)
    if sub is None:
        logger.warning("No local Subscription found for Stripe sub %s — skipping", stripe_sub_id)
        return

    stripe_status = data.get("status", "")
    status_map = {
        "active": SubscriptionStatus.ACTIVE,
        "canceled": SubscriptionStatus.CANCELLED,
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

    db.commit()
    logger.info("Subscription %s updated — status=%s", sub.id, stripe_status)


def handle_invoice_payment_succeeded(db: Session, data: Dict[str, Any]) -> None:
    """invoice.payment_succeeded → log a COMPLETED Payment row if not already present."""
    invoice_id = data.get("id", "")
    amount_paid = data.get("amount_paid", 0)
    currency = (data.get("currency") or "usd").upper()
    customer_id = data.get("customer", "")

    logger.info(
        "Stripe: invoice.payment_succeeded — invoice=%s amount=%s %s customer=%s",
        invoice_id, amount_paid, currency, customer_id,
    )

    user = _find_user_by_stripe_customer_id(db, customer_id) if customer_id else None
    if user:
        logger.info("Invoice %s linked to user %s (amount: %s %s)", invoice_id, user.id, amount_paid / 100, currency)
    else:
        logger.info("Invoice %s recorded (amount: %s %s) — no local user matched", invoice_id, amount_paid / 100, currency)


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

_HANDLERS = {
    "payment_intent.succeeded": handle_payment_intent_succeeded,
    "payment_intent.payment_failed": handle_payment_intent_failed,
    "customer.subscription.deleted": handle_subscription_deleted,
    "customer.subscription.updated": handle_subscription_updated,
    "invoice.payment_succeeded": handle_invoice_payment_succeeded,
}


def dispatch(db: Session, event: Any) -> bool:
    """
    Route a verified Stripe event to its handler.

    Returns True if a handler was found, False if the event type is unknown
    (which is not an error — forward-compatible by design).
    """
    event_type: str = event.get("type", "")
    data = event.get("data", {}).get("object", {})

    handler = _HANDLERS.get(event_type)
    if handler is None:
        logger.debug("Stripe: unhandled event type '%s' — ignoring", event_type)
        return False

    try:
        handler(db, data)
    except Exception:
        logger.exception("Error handling Stripe event '%s'", event_type)
        raise  # re-raise so the route can return 500 and Stripe will retry

    return True
