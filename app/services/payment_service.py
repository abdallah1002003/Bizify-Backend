import uuid
from decimal import Decimal
from typing import Any, Optional

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core import paymob_client, paypal_client
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.repositories.billing_repo import payment_repo, plan_repo, ppf_credit_repo, subscription_repo
from app.repositories.usage_repo import usage_repo


def get_active_plans(db: Session) -> list[Plan]:
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


async def create_paypal_order(plan_id: uuid.UUID, db: Session) -> dict[str, Any]:
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
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PayPal payment is currently unavailable. Please check your PayPal configuration or try again later.",
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
) -> dict[str, Any]:
    """Capture a PayPal payment and persist billing records."""
    plan = get_plan_or_404(plan_id, db)

    try:
        capture_result = await paypal_client.capture_order(order_id)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"PayPal capture error: {exc.response.text}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PayPal payment capture is currently unavailable. Please contact support.",
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


async def handle_webhook(event_type: str, resource: dict[str, Any], db: Session) -> None:
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


# ─────────────────────────────────────────────
#  Paymob – Visa / Mastercard
# ─────────────────────────────────────────────

async def create_paymob_payment(
    plan_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session,
    billing_data: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    """
    Initiate a Paymob card payment for the selected plan.

    Executes Paymob's 3-step flow (auth → order → payment key) and returns
    the iframe URL that the frontend should render for the cardholder.

    A `pending` Payment record is persisted immediately so we can reconcile
    the transaction when Paymob fires its webhook callback.
    """
    plan = get_plan_or_404(plan_id, db)

    # Sensible defaults for `billing_data` (Paymob requires these fields).
    billing_data = billing_data or {
        "apartment":       "NA",
        "email":           "NA",
        "floor":           "NA",
        "first_name":      "Bizify",
        "street":          "NA",
        "building":        "NA",
        "phone_number":    "NA",
        "shipping_method": "NA",
        "postal_code":     "NA",
        "city":            "NA",
        "country":         "EG",
        "last_name":       "User",
        "state":           "NA",
    }

    try:
        result = await paymob_client.create_card_payment(
            amount=plan.price,
            currency="EGP",
            merchant_order_id=str(plan.id),
            billing_data=billing_data,
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Card payment is currently unavailable. Please use PayPal or contact support.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Card payment is currently unavailable. Please use PayPal or contact support.",
        ) from exc

    # Create an active subscription (or upgrade the existing one) immediately.
    subscription = subscription_repo.create_or_update(
        db,
        user_id=user_id,
        plan_id=plan.id,
        commit=False,
    )

    # Persist a pending payment – will be updated to `succeeded` via webhook.
    payment = payment_repo.create_paymob_payment(
        db,
        user_id=user_id,
        subscription_id=subscription.id,
        amount=plan.price,
        currency="EGP",
        paymob_order_id=result["paymob_order_id"],
        status="pending",
        commit=True,
    )
    db.refresh(subscription)

    return {
        "payment_id":      payment.id,
        "subscription_id": subscription.id,
        "paymob_order_id": result["paymob_order_id"],
        "iframe_url":      result["iframe_url"],
    }


# ─────────────────────────────────────────────
#  Pay-Per-Feature (PPF) – one-time section purchase
# ─────────────────────────────────────────────

PPF_PRICE_PER_SECTION = Decimal("135.00")   # EGP — midpoint of 120-150 range


async def create_ppf_paymob_payment(
    quantity: int,
    user_id: uuid.UUID,
    db: Session,
    billing_data: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    """Initiate a Paymob card payment for `quantity` PPF sections."""
    total = PPF_PRICE_PER_SECTION * quantity

    billing_data = billing_data or {
        "apartment": "NA", "email": "NA", "floor": "NA",
        "first_name": "Bizify", "street": "NA", "building": "NA",
        "phone_number": "NA", "shipping_method": "NA", "postal_code": "NA",
        "city": "NA", "country": "EG", "last_name": "User", "state": "NA",
    }

    try:
        result = await paymob_client.create_card_payment(
            amount=total,
            currency="EGP",
            merchant_order_id=f"ppf-{user_id}-{quantity}",
            billing_data=billing_data,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Card payment unavailable. Please try again.",
        ) from exc

    credit = ppf_credit_repo.create_pending(
        db,
        user_id=user_id,
        quantity=quantity,
        amount=total,
        payment_method="paymob",
        payment_ref=result["paymob_order_id"],
    )

    return {
        "ppf_credit_id":  credit.id,
        "quantity":        quantity,
        "amount":          total,
        "paymob_order_id": result["paymob_order_id"],
        "iframe_url":      result["iframe_url"],
    }


async def create_ppf_paypal_payment(
    quantity: int,
    user_id: uuid.UUID,
    db: Session,
) -> dict[str, Any]:
    """Create a PayPal order for `quantity` PPF sections."""
    total = PPF_PRICE_PER_SECTION * quantity

    try:
        order = await paypal_client.create_order(
            amount=str(total),
            currency="USD",
            plan_id=f"ppf-{quantity}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="PayPal payment unavailable. Please try again.",
        ) from exc

    approval_url = next(
        (l["href"] for l in order.get("links", []) if l["rel"] == "approve"), None
    )
    if not approval_url:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="PayPal did not return an approval URL.")

    credit = ppf_credit_repo.create_pending(
        db,
        user_id=user_id,
        quantity=quantity,
        amount=total,
        payment_method="paypal",
        payment_ref=order["id"],
    )

    return {
        "ppf_credit_id": credit.id,
        "quantity":       quantity,
        "amount":         total,
        "order_id":       order["id"],
        "approval_url":   approval_url,
    }


async def capture_ppf_paypal_payment(
    order_id: str,
    user_id: uuid.UUID,
    db: Session,
) -> dict[str, Any]:
    """Capture a PPF PayPal order and credit the user's sections."""
    try:
        capture_result = await paypal_client.capture_order(order_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="PayPal capture failed.") from exc

    if capture_result.get("status") != "COMPLETED":
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED,
                            detail="Payment not completed.")

    credit = ppf_credit_repo.get_by_payment_ref(db, order_id)
    if not credit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="PPF credit record not found.")

    ppf_credit_repo.confirm(db, credit)
    usage_repo.add_ppf_sections(db, user_id, credit.quantity)

    return {
        "ppf_credit_id": credit.id,
        "quantity":       credit.quantity,
        "status":         "succeeded",
    }


async def handle_paymob_webhook(data: dict[str, Any], db: Session) -> None:
    """
    Process Paymob's Transaction Processed Callback.

    Validates the HMAC signature, then marks the Payment and Subscription
    as `succeeded` / active when Paymob reports a successful transaction.
    """
    if not paymob_client.verify_hmac(data):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Paymob HMAC signature.",
        )

    obj = data.get("obj", {})
    is_success: bool = obj.get("success", False)
    paymob_order_id = str(obj.get("order", {}).get("id", ""))
    transaction_id  = str(obj.get("id", ""))

    if not paymob_order_id:
        return

    # Check if this is a PPF payment first
    ppf_credit = ppf_credit_repo.get_by_payment_ref(db, paymob_order_id)
    if ppf_credit:
        if is_success and ppf_credit.status != "succeeded":
            ppf_credit_repo.confirm(db, ppf_credit)
            usage_repo.add_ppf_sections(db, ppf_credit.user_id, ppf_credit.quantity)
        return

    payment = payment_repo.get_by_paymob_order(db, paymob_order_id)
    if not payment:
        return

    new_status = "succeeded" if is_success else "failed"
    payment.status                = new_status
    payment.paymob_transaction_id = transaction_id
    db.add(payment)

    # Activate the linked subscription on success.
    if is_success and payment.subscription_id:
        from app.models.subscription import SubscriptionStatus  # avoid circular import
        subscription = db.get(Subscription, payment.subscription_id)
        if subscription:
            subscription.status = SubscriptionStatus.ACTIVE
            db.add(subscription)

    db.commit()
