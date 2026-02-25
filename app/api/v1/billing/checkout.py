# ruff: noqa
"""
Stripe Checkout Session endpoint.

POST /api/v1/billing/checkout
"""

import logging

import stripe
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.dependencies import get_current_active_user
from app.db.database import get_db
from app.models.billing.billing import Plan
import app.models as models
from config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class CheckoutRequest(BaseModel):
    plan_id: UUID = Field(..., description="ID of the Plan to subscribe to")
    success_url: str = Field(
        default_factory=lambda: f"{settings.FRONTEND_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
        description="URL to redirect to after successful payment",
    )
    cancel_url: str = Field(
        default_factory=lambda: f"{settings.FRONTEND_URL}/billing/cancel",
        description="URL to redirect to if the user cancels",
    )


class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str


@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    summary="Create Stripe Checkout Session",
)
def create_checkout_session(  # type: ignore
    body: CheckoutRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Create a Stripe Checkout Session for a billing plan.

    Returns a ``checkout_url`` — redirect the client to this URL.
    Stripe will redirect back to ``success_url`` or ``cancel_url`` when done.

    Requires ``STRIPE_ENABLED=true`` and ``STRIPE_SECRET_KEY`` in environment.
    """
    if not settings.STRIPE_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Stripe payments are not enabled on this server.",
        )

    # Fetch the plan
    plan = db.query(Plan).filter(Plan.id == body.plan_id, Plan.is_active == True).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found or inactive")

    stripe.api_key = settings.STRIPE_SECRET_KEY

    # Build or reuse a Stripe Customer for this user
    customer_id = current_user.stripe_customer_id
    if not customer_id:
        try:
            customer = stripe.Customer.create(
                email=current_user.email,
                name=current_user.name,
                metadata={"user_id": str(current_user.id)},
            )
            customer_id = customer.id
            current_user.stripe_customer_id = customer_id
            db.commit()
        except stripe.error.StripeError as exc:
            logger.error("Stripe customer creation failed for user %s: %s", current_user.id, exc)
            raise HTTPException(status_code=502, detail="Failed to create Stripe customer") from exc

    if plan.stripe_price_id:
        line_item = {
            "price": plan.stripe_price_id,
            "quantity": 1,
        }
    else:
        unit_amount = int(round(plan.price * 100))
        line_item = {
            "price_data": {
                "currency": settings.DEFAULT_CURRENCY.lower(),
                "unit_amount": unit_amount,
                "product_data": {
                    "name": plan.name,
                    "description": f"{settings.APP_NAME} {plan.name} Plan",
                },
                "recurring": {"interval": plan.billing_cycle or "month"},
            },
            "quantity": 1,
        }

    try:
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[line_item],  # type: ignore
            mode="subscription",
            success_url=body.success_url,
            cancel_url=body.cancel_url,
            metadata={
                "user_id": str(current_user.id),
                "plan_id": str(plan.id),
            },
        )
    except stripe.error.StripeError as exc:
        logger.error("Stripe Checkout Session creation failed: %s", exc)
        raise HTTPException(status_code=502, detail="Failed to create Stripe Checkout Session") from exc

    logger.info(
        "Stripe Checkout Session created: session=%s user=%s plan=%s",
        session.id, current_user.id, plan.id,
    )

    return CheckoutResponse(checkout_url=session.url, session_id=session.id)  # type: ignore
