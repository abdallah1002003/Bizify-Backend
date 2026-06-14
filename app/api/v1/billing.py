import json
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.core import paypal_client
from app.repositories.usage_repo import usage_repo
from app.models.user import User
from app.schemas.billing import (
    CaptureRequest,
    CaptureResponse,
    InstapayPPFRequest,
    InstapayPPFResponse,
    InstapaySubscribeRequest,
    InstapaySubscribeResponse,
    OrderCreate,
    OrderResponse,
    PaymobCheckoutRequest,
    PaymobCheckoutResponse,
    PlanRead,
    PPFBalanceResponse,
    PPFCaptureRequest,
    PPFPaymobResponse,
    PPFPayPalResponse,
    PPFPurchaseRequest,
    SubscriptionRead,
)
from app.services import payment_service

router = APIRouter()


@router.get("/plans", response_model=list[PlanRead])
def list_plans(db: Session = Depends(get_db)) -> list[PlanRead]:
    """Return all active subscription plans."""
    return payment_service.get_active_plans(db)


@router.post("/paypal/subscribe", response_model=OrderResponse)
async def create_subscription_order(
    body: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Create a PayPal order for the chosen plan."""
    result = await payment_service.create_paypal_order(
        plan_id=body.plan_id,
        user_id=current_user.id,
        db=db,
    )
    return result


@router.post("/paypal/capture", response_model=CaptureResponse)
async def capture_subscription_payment(
    body: CaptureRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Capture a PayPal order after user approval."""
    result = await payment_service.capture_payment(
        order_id=body.order_id,
        plan_id=body.plan_id,
        user_id=current_user.id,
        db=db,
    )
    return result


@router.get("/subscription", response_model=SubscriptionRead)
def get_my_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Return the authenticated user's active subscription."""
    subscription = payment_service.get_user_subscription(current_user.id, db)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found.",
        )
    return subscription


@router.delete("/subscription", status_code=status.HTTP_200_OK)
def cancel_my_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Cancel the authenticated user's active subscription."""
    payment_service.cancel_subscription(current_user.id, db)
    return {"message": "Subscription cancelled successfully."}


@router.post("/paypal/webhook", status_code=status.HTTP_200_OK)
async def paypal_webhook(
    request: Request,
    db: Session = Depends(get_db),
    paypal_transmission_id: Optional[str] = Header(None, alias="paypal-transmission-id"),
    paypal_transmission_time: Optional[str] = Header(None, alias="paypal-transmission-time"),
    paypal_cert_url: Optional[str] = Header(None, alias="paypal-cert-url"),
    paypal_auth_algo: Optional[str] = Header(None, alias="paypal-auth-algo"),
    paypal_transmission_sig: Optional[str] = Header(None, alias="paypal-transmission-sig"),
) -> Any:
    """Receive and verify PayPal webhook events."""
    body = await request.body()
    is_valid = await paypal_client.verify_webhook_signature(
        transmission_id=paypal_transmission_id,
        transmission_time=paypal_transmission_time,
        cert_url=paypal_cert_url,
        auth_algo=paypal_auth_algo,
        actual_signature=paypal_transmission_sig,
        webhook_body=body,
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PayPal webhook signature.",
        )

    event = json.loads(body)
    event_type = event.get("event_type", "")
    resource = event.get("resource", {})
    await payment_service.handle_webhook(event_type, resource, db)
    return {"message": "Webhook received."}




@router.post("/paymob/subscribe", response_model=PaymobCheckoutResponse)
async def create_paymob_subscription(
    body: PaymobCheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Initiate a Paymob card payment for the chosen plan.

    Returns an iframe URL that the frontend should render inside an <iframe>
    so the cardholder can enter their Visa / Mastercard details.
    """
    billing_data: Optional[dict] = None
    if any([body.first_name, body.last_name, body.email, body.phone_number]):
        billing_data = {
            "apartment":       "NA",
            "email":           body.email or "NA",
            "floor":           "NA",
            "first_name":      body.first_name or "NA",
            "street":          "NA",
            "building":        "NA",
            "phone_number":    body.phone_number or "NA",
            "shipping_method": "NA",
            "postal_code":     "NA",
            "city":            "NA",
            "country":         "EG",
            "last_name":       body.last_name or "NA",
            "state":           "NA",
        }

    result = await payment_service.create_paymob_payment(
        plan_id=body.plan_id,
        user_id=current_user.id,
        db=db,
        billing_data=billing_data,
    )
    return result


# ─────────────────────────────────────────────
#  Pay-Per-Feature (PPF) endpoints
# ─────────────────────────────────────────────

@router.get("/ppf/balance", response_model=PPFBalanceResponse)
def get_ppf_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Return how many PPF section credits the user has purchased and consumed."""
    record = usage_repo.get_or_create(db, current_user.id)
    purchased = record.ppf_purchased or 0
    used      = record.ppf_used or 0
    return {"purchased": purchased, "used": used, "remaining": max(purchased - used, 0)}


@router.post("/ppf/paymob", response_model=PPFPaymobResponse)
async def buy_ppf_paymob(
    body: PPFPurchaseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Initiate a Paymob card payment to purchase PPF section credits."""
    if body.quantity < 1 or body.quantity > 10:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="quantity must be between 1 and 10.")
    billing_data = None
    if any([body.first_name, body.last_name, body.email, body.phone_number]):
        billing_data = {
            "apartment": "NA", "email": body.email or "NA", "floor": "NA",
            "first_name": body.first_name or "NA", "street": "NA", "building": "NA",
            "phone_number": body.phone_number or "NA", "shipping_method": "NA",
            "postal_code": "NA", "city": "NA", "country": "EG",
            "last_name": body.last_name or "NA", "state": "NA",
        }
    return await payment_service.create_ppf_paymob_payment(
        quantity=body.quantity, user_id=current_user.id, db=db,
        feature_key=body.feature_key, billing_data=billing_data,
        total_amount_override=body.total_amount_egp,
    )


@router.post("/ppf/paypal", response_model=PPFPayPalResponse)
async def buy_ppf_paypal(
    body: PPFPurchaseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Create a PayPal order to purchase PPF section credits."""
    if body.quantity < 1 or body.quantity > 10:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="quantity must be between 1 and 10.")
    return await payment_service.create_ppf_paypal_payment(
        quantity=body.quantity, user_id=current_user.id, db=db,
        feature_key=body.feature_key, total_amount_override=body.total_amount_egp,
    )


@router.post("/ppf/paypal/capture")
async def capture_ppf_paypal(
    body: PPFCaptureRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Capture an approved PayPal order and credit the PPF sections."""
    return await payment_service.capture_ppf_paypal_payment(
        order_id=body.order_id, user_id=current_user.id, db=db
    )


# ─────────────────────────────────────────────
#  InstaPay – manual reference flow
# ─────────────────────────────────────────────

@router.post("/instapay/subscribe", response_model=InstapaySubscribeResponse, status_code=status.HTTP_202_ACCEPTED)
def instapay_subscribe(
    body: InstapaySubscribeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Submit an InstaPay subscription payment for admin review."""
    return payment_service.create_instapay_subscription(
        plan_id=body.plan_id,
        user_id=current_user.id,
        reference=body.reference,
        db=db,
    )


@router.post("/instapay/ppf", response_model=InstapayPPFResponse, status_code=status.HTTP_202_ACCEPTED)
def instapay_ppf(
    body: InstapayPPFRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Submit an InstaPay PPF purchase for admin review."""
    if body.quantity < 1 or body.quantity > 10:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="quantity must be between 1 and 10.")
    return payment_service.create_instapay_ppf(
        quantity=body.quantity,
        user_id=current_user.id,
        reference=body.reference,
        db=db,
        feature_key=body.feature_key,
        total_amount_override=body.total_amount_egp,
    )


@router.post("/paymob/webhook", status_code=status.HTTP_200_OK)
async def paymob_webhook(
    request: Request,
    db: Session = Depends(get_db),
) -> Any:
    """
    Receive Transaction Processed Callbacks from Paymob.

    Paymob signs the payload with an HMAC-SHA512 hash using your HMAC secret
    (configured as PAYMOB_HMAC_SECRET in .env). The service layer validates
    this signature before processing the event.
    """
    data = await request.json()
    await payment_service.handle_paymob_webhook(data, db)
    return {"message": "Paymob webhook received."}

