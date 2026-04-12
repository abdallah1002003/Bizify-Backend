import json
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.core import paypal_client
from app.models.user import User
from app.schemas.billing import (
    CaptureRequest,
    CaptureResponse,
    OrderCreate,
    OrderResponse,
    PlanRead,
    SubscriptionRead,
)
from app.services import payment_service

router = APIRouter()


@router.get("/plans", response_model=List[PlanRead])
def list_plans(db: Session = Depends(get_db)) -> List[PlanRead]:
    """Return all active subscription plans."""
    return payment_service.get_active_plans(db)


@router.post("/subscribe", response_model=OrderResponse)
async def create_subscription_order(
    body: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Create a PayPal order for the chosen plan."""
    result = await payment_service.create_paypal_order(
        plan_id=body.plan_id,
        db=db,
    )
    return result


@router.post("/capture", response_model=CaptureResponse)
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


@router.post("/webhook", status_code=status.HTTP_200_OK)
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
