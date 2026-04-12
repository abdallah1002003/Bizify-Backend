import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core import paypal_client
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.repositories.billing_repo import payment_repo, plan_repo, subscription_repo


def get_active_plans(db: Session) -> List[Plan]:
    """Return all active subscription plans."""
    return plan_repo.get_active_plans(db)


def get_plan_or_404(plan_id: uuid.UUID, db: Session) -> Plan:
    """Fetch an active plan or raise 404."""
    plan = plan_repo.get_active_by_id(db, plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found or inactive.",
        )
    return plan


async def create_paypal_order(plan_id: uuid.UUID, db: Session) -> Dict[str, Any]:
    """Create a PayPal order for the selected plan."""
    plan = get_plan_or_404(plan_id, db)

    try:
        order = await paypal_client.create_order(
            amount=str(plan.price),
            currency="USD",
            plan_id=str(plan.id),
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"PayPal error: {exc.response.text}",
        ) from exc

    approval_url = next(
        (link["href"] for link in order.get("links", []) if link["rel"] == "approve"),
        None,
    )
    if not approval_url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="PayPal did not return an approval URL.",
        )

    return {
        "order_id": order["id"],
        "approval_url": approval_url,
        "status": order["status"],
    }


async def capture_payment(
    order_id: str,
    plan_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session,
) -> Dict[str, Any]:
    """Capture a PayPal payment and persist billing records."""
    plan = get_plan_or_404(plan_id, db)

    try:
        capture_result = await paypal_client.capture_order(order_id)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"PayPal capture error: {exc.response.text}",
        ) from exc

    capture_status = capture_result.get("status")
    if capture_status != "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Payment not completed. PayPal status: {capture_status}",
        )

    purchase_unit = capture_result["purchase_units"][0]
    capture_data = purchase_unit["payments"]["captures"][0]
    capture_id = capture_data["id"]
    captured_amount = Decimal(capture_data["amount"]["value"])
    captured_currency = capture_data["amount"]["currency_code"]

    subscription = subscription_repo.create_or_update(
        db,
        user_id=user_id,
        plan_id=plan.id,
        commit=False,
    )
    payment = payment_repo.create_payment(
        db,
        user_id=user_id,
        subscription_id=subscription.id,
        amount=captured_amount,
        currency=captured_currency,
        paypal_order_id=order_id,
        paypal_capture_id=capture_id,
        commit=True,
    )
    db.refresh(subscription)

    return {
        "payment_id": payment.id,
        "subscription_id": subscription.id,
        "status": "succeeded",
        "amount": captured_amount,
        "currency": captured_currency,
    }


def get_user_subscription(user_id: uuid.UUID, db: Session) -> Optional[Subscription]:
    """Return the user's active subscription, if any."""
    return subscription_repo.get_active_by_user(db, user_id)


def cancel_subscription(user_id: uuid.UUID, db: Session) -> Subscription:
    """Cancel the user's active subscription."""
    subscription = subscription_repo.get_active_by_user(db, user_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found.",
        )

    return subscription_repo.cancel(db, subscription)


async def handle_webhook(event_type: str, resource: Dict[str, Any], db: Session) -> None:
    """Process supported PayPal webhook events."""
    if event_type == "PAYMENT.CAPTURE.COMPLETED":
        capture_id = resource.get("id")
        if capture_id:
            payment = payment_repo.get_by_paypal_capture(db, capture_id)
            if payment and payment.status != "succeeded":
                payment_repo.update(
                    db,
                    db_obj=payment,
                    obj_in={"status": "succeeded"},
                )
        return

    if event_type == "BILLING.SUBSCRIPTION.CANCELLED":
        paypal_sub_id = resource.get("id")
        if not paypal_sub_id:
            return

        subscription = subscription_repo.get_by_paypal_subscription(db, paypal_sub_id)
        if subscription:
            subscription_repo.cancel(db, subscription)
