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
from app.repositories.usage_repo import usage_repo, PRO_MONTHLY_CREDITS, PREMIUM_MONTHLY_CREDITS


def _credits_for_plan(plan: Plan) -> int:
    """Return the monthly credit allowance to apply when this plan activates."""
    name = (plan.name or "").lower()
    if "premium" in name:
        return PREMIUM_MONTHLY_CREDITS
    if "pro" in name:
        return PRO_MONTHLY_CREDITS
    return 15  # Free / unknown — baseline


def _provision_plan_credits(db: Session, user_id: uuid.UUID, plan: Plan) -> None:
    """Reset the user's credit period to match their newly activated plan."""
    usage_repo.set_plan_credits(db, user_id, _credits_for_plan(plan))


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


async def create_paypal_order(plan_id: uuid.UUID, user_id: uuid.UUID, db: Session) -> dict[str, Any]:
    """
    Create a PayPal order for the selected plan and persist a PENDING
    subscription + payment so the order_id is server-bound to this plan/amount.
    Capture later reads that record instead of trusting a client plan_id.
    """
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
            detail="PayPal payment is currently unavailable. Please try again later.",
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

    # Bind this order to the chosen plan server-side via a pending subscription.
    pending_sub = subscription_repo.create_pending(
        db, user_id=user_id, plan_id=plan.id, commit=False,
    )
    payment_repo.create_pending_paypal_payment(
        db,
        user_id=user_id,
        subscription_id=pending_sub.id,
        amount=plan.price,
        currency="USD",
        paypal_order_id=order["id"],
        commit=True,
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
    """
    Capture a PayPal payment and activate the subscription.

    SECURITY: the plan is derived from the server-side pending payment that was
    created with the order — the client-supplied `plan_id` is intentionally
    ignored so a user cannot pay for a cheap plan and receive an expensive one.
    The captured amount is also verified against the plan price.
    """
    payment = payment_repo.get_by_paypal_order(db, order_id)
    if not payment or payment.subscription_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment order not found.",
        )
    if payment.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This order does not belong to the current user.",
        )

    subscription = db.get(Subscription, payment.subscription_id)
    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription for this order no longer exists.",
        )

    # Idempotency — if this order was already captured, don't double-activate.
    if payment.status == "succeeded":
        return {
            "payment_id": payment.id,
            "subscription_id": subscription.id,
            "status": "succeeded",
            "amount": payment.amount,
            "currency": payment.currency,
        }

    plan = get_plan_or_404(subscription.plan_id, db)

    try:
        capture_result = await paypal_client.capture_order(order_id)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="PayPal payment capture is currently unavailable. Please contact support.",
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

    # Verify the captured amount matches the server-side plan price.
    if captured_amount != Decimal(str(plan.price)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Captured amount does not match the plan price.",
        )

    payment.status = "succeeded"
    payment.paypal_capture_id = capture_id
    payment.amount = captured_amount
    payment.currency = captured_currency
    db.add(payment)

    subscription_repo.activate(db, subscription, commit=False)
    _provision_plan_credits(db, subscription.user_id, plan)
    db.commit()
    db.refresh(subscription)
    db.refresh(payment)

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
            # Must be unique per transaction — Paymob rejects duplicate
            # merchant_order_ids, so we never reuse the plan id here.
            merchant_order_id=f"sub-{user_id}-{uuid.uuid4().hex[:16]}",
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

    # Create a PENDING subscription — it is NOT active until Paymob confirms the
    # payment via webhook, so the user does not get paid features for free by
    # merely opening the card iframe.
    subscription = subscription_repo.create_pending(
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

from app.constants.credit_costs import PAYG_FEATURE_PRICES, PAYG_TIER_2

# Kept for backward-compatibility; new code should use PAYG_FEATURE_PRICES.
PPF_PRICE_PER_SECTION = PAYG_TIER_2


def get_ppf_price(feature_key: str) -> Decimal:
    """Return the EGP price for a single PAYG feature run."""
    return PAYG_FEATURE_PRICES.get(feature_key, PAYG_TIER_2)


async def create_ppf_paymob_payment(
    quantity: int,
    user_id: uuid.UUID,
    db: Session,
    feature_key: str = "unknown",
    billing_data: Optional[dict[str, str]] = None,
    total_amount_override: Optional[Decimal] = None,
) -> dict[str, Any]:
    """Initiate a Paymob card payment for `quantity` PAYG feature runs."""
    unit_price = get_ppf_price(feature_key)
    total = total_amount_override if total_amount_override is not None else (unit_price * quantity)

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
            merchant_order_id=f"ppf-{user_id}-{feature_key}-{quantity}",
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
        "feature_key":     feature_key,
        "quantity":        quantity,
        "unit_price":      unit_price,
        "amount":          total,
        "paymob_order_id": result["paymob_order_id"],
        "iframe_url":      result["iframe_url"],
    }


async def create_ppf_paypal_payment(
    quantity: int,
    user_id: uuid.UUID,
    db: Session,
    feature_key: str = "unknown",
    total_amount_override: Optional[Decimal] = None,
) -> dict[str, Any]:
    """Create a PayPal order for `quantity` PAYG feature runs."""
    unit_price = get_ppf_price(feature_key)
    total = total_amount_override if total_amount_override is not None else (unit_price * quantity)

    try:
        order = await paypal_client.create_order(
            amount=str(total),
            currency="USD",
            plan_id=f"ppf-{feature_key}-{quantity}",
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
        "feature_key":    feature_key,
        "quantity":       quantity,
        "unit_price":     unit_price,
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
    if credit.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="This order does not belong to the current user.")
    # Idempotency — already credited.
    if credit.status == "succeeded":
        return {"ppf_credit_id": credit.id, "quantity": credit.quantity, "status": "succeeded"}

    # Verify the captured amount matches the recorded purchase amount.
    try:
        captured_amount = Decimal(
            capture_result["purchase_units"][0]["payments"]["captures"][0]["amount"]["value"]
        )
    except (KeyError, IndexError, TypeError):
        captured_amount = None
    if captured_amount is not None and captured_amount != Decimal(str(credit.amount_paid)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Captured amount does not match the purchase amount.")

    ppf_credit_repo.confirm(db, credit)
    usage_repo.add_ppf_sections(db, user_id, credit.quantity)

    return {
        "ppf_credit_id": credit.id,
        "quantity":       credit.quantity,
        "status":         "succeeded",
    }


# ─────────────────────────────────────────────
#  InstaPay – manual reference flow
# ─────────────────────────────────────────────

def create_instapay_subscription(
    plan_id: uuid.UUID,
    user_id: uuid.UUID,
    reference: str,
    db: Session,
) -> dict[str, Any]:
    """
    Record an InstaPay subscription payment for admin review.
    Creates a PENDING subscription + PENDING payment with the reference number.
    Nothing is activated until an admin approves it.
    """
    ref = (reference or "").strip()
    if not ref.isdigit() or len(ref) != 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="InstaPay reference number must be exactly 12 digits.",
        )
    plan = get_plan_or_404(plan_id, db)

    pending_sub = subscription_repo.create_pending(
        db, user_id=user_id, plan_id=plan.id, commit=False,
    )
    payment = payment_repo.create_instapay_payment(
        db,
        user_id=user_id,
        subscription_id=pending_sub.id,
        amount=plan.price,
        instapay_reference=ref,
        commit=True,
    )
    db.refresh(pending_sub)

    return {
        "payment_id":      payment.id,
        "subscription_id": pending_sub.id,
        "status":          "pending_review",
    }


def create_instapay_ppf(
    quantity: int,
    user_id: uuid.UUID,
    reference: str,
    db: Session,
    feature_key: str = "unknown",
    total_amount_override: Optional[Decimal] = None,
) -> dict[str, Any]:
    """
    Record an InstaPay PPF purchase for admin review.
    Creates a pending PPFCredit with payment_method='instapay'.
    Credits are added only after admin approval.
    """
    ref = (reference or "").strip()
    if not ref.isdigit() or len(ref) != 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="InstaPay reference number must be exactly 12 digits.",
        )
    unit_price = get_ppf_price(feature_key)
    total = total_amount_override if total_amount_override is not None else (unit_price * quantity)

    credit = ppf_credit_repo.create_pending(
        db,
        user_id=user_id,
        quantity=quantity,
        amount=total,
        payment_method="instapay",
        payment_ref=ref,
    )
    return {
        "ppf_credit_id": credit.id,
        "quantity":       quantity,
        "amount":         total,
        "status":         "pending_review",
    }


def approve_instapay_payment(payment_id: uuid.UUID, db: Session) -> dict[str, Any]:
    """Admin: approve an InstaPay subscription payment → activate subscription."""
    payment = db.get(payment_repo.model, payment_id)
    if not payment or payment.instapay_reference is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="InstaPay payment not found.")
    if payment.status == "succeeded":
        return {"status": "already_approved"}

    payment.status = "succeeded"
    db.add(payment)

    if payment.subscription_id:
        subscription = db.get(Subscription, payment.subscription_id)
        if subscription:
            subscription_repo.activate(db, subscription, commit=False)
            plan = plan_repo.get_active_by_id(db, subscription.plan_id)
            if plan:
                _provision_plan_credits(db, subscription.user_id, plan)

    db.commit()
    return {"status": "approved"}


def reject_instapay_payment(payment_id: uuid.UUID, db: Session) -> dict[str, Any]:
    """Admin: reject an InstaPay subscription payment → cancel pending subscription."""
    payment = db.get(payment_repo.model, payment_id)
    if not payment or payment.instapay_reference is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="InstaPay payment not found.")
    if payment.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment is not pending.")

    payment.status = "failed"
    db.add(payment)

    if payment.subscription_id:
        subscription = db.get(Subscription, payment.subscription_id)
        if subscription:
            from app.models.subscription import SubscriptionStatus
            if subscription.status != SubscriptionStatus.ACTIVE:
                subscription_repo.cancel(db, subscription, commit=False)

    db.commit()
    return {"status": "rejected"}


def approve_instapay_ppf(ppf_credit_id: uuid.UUID, db: Session) -> dict[str, Any]:
    """Admin: approve an InstaPay PPF credit → add sections to user balance."""
    credit = db.get(ppf_credit_repo.model, ppf_credit_id)
    if not credit or credit.payment_method != "instapay":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="InstaPay PPF credit not found.")
    if credit.status == "succeeded":
        return {"status": "already_approved"}

    ppf_credit_repo.confirm(db, credit)
    usage_repo.add_ppf_sections(db, credit.user_id, credit.quantity)
    return {"status": "approved"}


def reject_instapay_ppf(ppf_credit_id: uuid.UUID, db: Session) -> dict[str, Any]:
    """Admin: reject an InstaPay PPF credit."""
    credit = db.get(ppf_credit_repo.model, ppf_credit_id)
    if not credit or credit.payment_method != "instapay":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="InstaPay PPF credit not found.")
    if credit.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PPF credit is not pending.")

    credit.status = "failed"
    db.add(credit)
    db.commit()
    return {"status": "rejected"}


def list_pending_instapay(db: Session) -> list[dict[str, Any]]:
    """Return all pending InstaPay payments (subscriptions + PPF) for admin review."""
    from app.models.user import User as UserModel

    results: list[dict[str, Any]] = []

    # Subscription payments
    for payment in payment_repo.get_pending_instapay(db):
        user = db.get(UserModel, payment.user_id)
        plan_name = None
        if payment.subscription_id:
            sub = db.get(Subscription, payment.subscription_id)
            if sub:
                plan = plan_repo.get_active_by_id(db, sub.plan_id)
                plan_name = plan.name if plan else None
        results.append({
            "id":         payment.id,
            "type":       "subscription",
            "user_id":    payment.user_id,
            "user_email": user.email if user else None,
            "amount":     payment.amount,
            "currency":   payment.currency,
            "reference":  payment.instapay_reference,
            "plan_name":  plan_name,
            "quantity":   None,
            "created_at": payment.created_at,
        })

    # PPF credits
    for credit in ppf_credit_repo.get_pending_instapay(db):
        user = db.get(UserModel, credit.user_id)
        results.append({
            "id":         credit.id,
            "type":       "ppf",
            "user_id":    credit.user_id,
            "user_email": user.email if user else None,
            "amount":     credit.amount_paid,
            "currency":   credit.currency,
            "reference":  credit.payment_ref,
            "plan_name":  None,
            "quantity":   credit.quantity,
            "created_at": credit.created_at,
        })

    results.sort(key=lambda x: x["created_at"])
    return results


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

    # Idempotency — ignore repeated callbacks for an already-settled payment.
    if payment.status == "succeeded":
        return

    new_status = "succeeded" if is_success else "failed"
    payment.status                = new_status
    payment.paymob_transaction_id = transaction_id
    db.add(payment)

    if payment.subscription_id:
        subscription = db.get(Subscription, payment.subscription_id)
        if subscription:
            if is_success:
                # Activate only now that money is confirmed received.
                subscription_repo.activate(db, subscription, commit=False)
                # Reset the user's credit allowance to match the new plan.
                activated_plan = plan_repo.get_active_by_id(db, subscription.plan_id)
                if activated_plan:
                    _provision_plan_credits(db, subscription.user_id, activated_plan)
            else:
                # Failed payment — discard the pending subscription so it never
                # lingers and is never treated as active.
                from app.models.subscription import SubscriptionStatus
                if subscription.status != SubscriptionStatus.ACTIVE:
                    subscription_repo.cancel(db, subscription, commit=False)

    db.commit()
