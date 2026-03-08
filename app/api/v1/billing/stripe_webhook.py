# ruff: noqa
"""
Stripe Webhook endpoint.

POST /api/v1/billing/webhooks/stripe

- No authentication header required (Stripe calls this unauthenticated).
- Signature is verified via stripe.Webhook.construct_event using
  STRIPE_WEBHOOK_SECRET from settings.
- Returns 400 on invalid payload/signature, 200 {"status": "ok"} on success.
- Unknown event types return 200 silently (forward-compatible).
"""

import logging

import stripe
from fastapi import APIRouter, Header, HTTPException, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_db
from app.services.billing.stripe_webhook_service import StripeWebhookService
from config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/stripe",
    summary="Stripe Webhook Receiver",
    status_code=200,
    # Stripe docs recommend returning 200 quickly; let the router handle errors.
)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(..., alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Receive and process Stripe webhook events.

    Verifies the ``Stripe-Signature`` header before processing to prevent
    spoofed events. Returns **400** if the signature is invalid.

    Poll this endpoint with the Stripe CLI for local development:

    ```
    stripe listen --forward-to localhost:8001/api/v1/billing/webhooks/stripe
    ```
    """
    if not settings.STRIPE_ENABLED:
        logger.debug("STRIPE_ENABLED=False — webhook call ignored")
        return {"status": "disabled"}

    raw_body = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload=raw_body,
            sig_header=stripe_signature,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except stripe.error.SignatureVerificationError as exc:
        logger.warning("Stripe webhook signature verification failed: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid Stripe signature") from exc
    except Exception as exc:
        logger.error("Stripe webhook payload error: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid webhook payload") from exc

    service = StripeWebhookService(db)
    await service.dispatch(event)
    return {"status": "ok", "event_type": event.get("type")}
