"""
Stripe Idempotency Key Utility.

This module provides deterministic, idempotency-key generation for outgoing
Stripe API calls (PaymentIntent, Subscription creation, Refunds, etc.).

## Why Idempotency Keys?
Stripe's API supports an ``Idempotency-Key`` HTTP header that makes any write
operation safe to retry. If the same key is passed twice, Stripe returns the
*original* response instead of creating a duplicate object. This protects
against race conditions, network timeouts, and accidental double-clicks.

## Usage Pattern
    ```python
    from app.services.billing.stripe_idempotency import make_key, StripeIdempotencyClient

    # Option 1: generate a key manually and pass to Stripe SDK
    key = make_key("create_payment_intent", user_id=user_id, amount_cents=1000)
    intent = stripe.PaymentIntent.create(
        amount=1000,
        currency="usd",
        idempotency_key=key,
    )

    # Option 2: use the convenience client (wraps the SDK call)
    client = StripeIdempotencyClient()
    intent = client.create_payment_intent(
        user_id=user_id,
        amount_cents=1000,
        currency="usd",
    )
    ```

## Key Space
Keys are deterministic hashes of the operation name + semantic parameters.
They are idempotent within a 24-hour window (Stripe's idempotency window).
To force a fresh call after 24 h, pass a custom ``date_str`` (YYYY-MM-DD).
"""
from __future__ import annotations

import hashlib
import logging
from datetime import date
from typing import Any, Dict, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


def make_key(
    operation: str,
    *,
    user_id: Optional[UUID] = None,
    subscription_id: Optional[UUID] = None,
    payment_id: Optional[UUID] = None,
    amount_cents: Optional[int] = None,
    extra: Optional[str] = None,
    date_str: Optional[str] = None,
) -> str:
    """Generate a deterministic Stripe idempotency key.

    The key is a truncated SHA-256 hash (48 hex chars) of all provided
    parameters. It is safe to pass as ``idempotency_key`` to any Stripe SDK
    call.

    Args:
        operation:       Human-readable operation name, e.g. ``"create_payment_intent"``.
        user_id:         The acting user's UUID (optional but strongly recommended).
        subscription_id: A related Subscription UUID (optional).
        payment_id:      A related Payment UUID (optional).
        amount_cents:    Monetary amount in the smallest currency unit (optional).
        extra:           Any additional discriminator string (optional).
        date_str:        Date in YYYY-MM-DD format for windowing (default: today UTC).

    Returns:
        A 48-character lowercase hex string suitable for Stripe's
        ``Idempotency-Key`` header.

    Example:
        >>> key = make_key("create_payment_intent", user_id=uid, amount_cents=999)
        >>> # "create_payment_intent:user=<uid>:amount=999:date=2026-02-25"
        >>> len(key)
        48
    """
    date_str = date_str or date.today().isoformat()

    parts: list[str] = [f"op={operation}", f"date={date_str}"]
    if user_id is not None:
        parts.append(f"user={user_id}")
    if subscription_id is not None:
        parts.append(f"sub={subscription_id}")
    if payment_id is not None:
        parts.append(f"pay={payment_id}")
    if amount_cents is not None:
        parts.append(f"amount={amount_cents}")
    if extra:
        parts.append(f"extra={extra}")

    raw = ":".join(parts)
    digest = hashlib.sha256(raw.encode()).hexdigest()[:48]
    logger.debug("Stripe idempotency key for '%s': %s (raw='%s')", operation, digest, raw)
    return digest


class StripeIdempotencyClient:
    """
    Thin wrapper around common Stripe write operations that automatically
    attaches idempotency keys.

    Intended for future use when Bizify initiates Stripe calls directly
    (e.g., server-side PaymentIntent creation, refunds).

    Current architecture is webhook-driven: Stripe initiates all state
    transitions. This client is provided for forward-compatibility.

    Example:
        >>> client = StripeIdempotencyClient()
        >>> intent = await client.create_payment_intent(
        ...     user_id=user_id,
        ...     amount_cents=2999,
        ...     currency="usd",
        ...     metadata={"subscription_id": str(sub_id)},
        ... )
    """

    async def create_payment_intent(
        self,
        user_id: UUID,
        amount_cents: int,
        currency: str = "usd",
        metadata: Optional[Dict[str, Any]] = None,
        extra: Optional[str] = None,
    ) -> Any:
        """Create a Stripe PaymentIntent with an idempotency key.

        Args:
            user_id:      UUID of the user initiating the payment.
            amount_cents: Amount in the smallest currency unit (e.g., 999 = $9.99).
            currency:     ISO 4217 currency code (default: "usd").
            metadata:     Optional dict forwarded to Stripe as metadata.
            extra:        Additional discriminator to allow multiple intents
                          for the same user/amount on the same day.

        Returns:
            ``stripe.PaymentIntent`` object.

        Raises:
            stripe.error.StripeError: On API or network errors.
            ImportError: If ``stripe`` is not installed.
        """
        import stripe  # lazy import — stripe is optional in dev

        idem_key = make_key(
            "create_payment_intent",
            user_id=user_id,
            amount_cents=amount_cents,
            extra=extra,
        )
        logger.info(
            "Creating Stripe PaymentIntent: user=%s amount=%d %s idem_key=%s",
            user_id, amount_cents, currency, idem_key,
        )
        return stripe.PaymentIntent.create(
            amount=amount_cents,
            currency=currency,
            metadata=metadata or {},
            idempotency_key=idem_key,
        )

    async def create_refund(
        self,
        payment_intent_id: str,
        amount_cents: Optional[int] = None,
        user_id: Optional[UUID] = None,
        extra: Optional[str] = None,
    ) -> Any:
        """Issue a Stripe Refund with an idempotency key.

        Args:
            payment_intent_id: Stripe PaymentIntent ID (``pi_...``).
            amount_cents:       Amount to refund (None = full refund).
            user_id:            UUID of the user (for key namespacing).
            extra:              Additional discriminator (e.g., "partial-1").

        Returns:
            ``stripe.Refund`` object.

        Raises:
            stripe.error.StripeError: On API or network errors.
        """
        import stripe  # lazy import

        idem_key = make_key(
            "create_refund",
            user_id=user_id,
            amount_cents=amount_cents,
            extra=extra or payment_intent_id,
        )
        logger.info(
            "Creating Stripe Refund: intent=%s amount=%s idem_key=%s",
            payment_intent_id, amount_cents, idem_key,
        )
        params: Dict[str, Any] = {"payment_intent": payment_intent_id}
        if amount_cents is not None:
            params["amount"] = amount_cents

        return stripe.Refund.create(**params, idempotency_key=idem_key)
