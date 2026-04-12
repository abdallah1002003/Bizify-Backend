"""
Pydantic schemas for the billing / payment module.
Covers Plans, PayPal order lifecycle, Payments, and Subscriptions.
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ─────────────────────────────────────────────
#  Plans
# ─────────────────────────────────────────────

class PlanRead(BaseModel):
    """
    Read-only view of a subscription plan.
    """
    id:            uuid.UUID
    name:          str
    price:         Decimal
    features_json: Optional[dict] = None
    is_active:     bool

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────
#  PayPal Order lifecycle
# ─────────────────────────────────────────────

class OrderCreate(BaseModel):
    """
    Request body to initiate a PayPal payment for a plan.
    """
    plan_id: uuid.UUID


class OrderResponse(BaseModel):
    """
    Response returned after creating a PayPal Order.
    The frontend should redirect the user to `approval_url`.
    """
    order_id:     str
    approval_url: str
    status:       str


class CaptureRequest(BaseModel):
    """
    Request body to capture (finalise) an approved PayPal Order.
    """
    order_id: str
    plan_id:  uuid.UUID


class CaptureResponse(BaseModel):
    """
    Response after a successful payment capture.
    """
    payment_id:      uuid.UUID
    subscription_id: uuid.UUID
    status:          str
    amount:          Decimal
    currency:        str


# ─────────────────────────────────────────────
#  Payments
# ─────────────────────────────────────────────

class PaymentRead(BaseModel):
    """
    Read-only view of a payment record.
    """
    id:                uuid.UUID
    user_id:           uuid.UUID
    subscription_id:   Optional[uuid.UUID] = None
    amount:            Decimal
    currency:          str
    status:            str
    paypal_order_id:   Optional[str] = None
    paypal_capture_id: Optional[str] = None
    created_at:        datetime

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────
#  Subscriptions
# ─────────────────────────────────────────────

class SubscriptionRead(BaseModel):
    """
    Read-only view of a user's active subscription.
    """
    id:                     uuid.UUID
    user_id:                uuid.UUID
    plan_id:                uuid.UUID
    status:                 str
    start_date:             datetime
    end_date:               Optional[datetime] = None
    paypal_subscription_id: Optional[str] = None
    plan:                   Optional[PlanRead] = None

    model_config = ConfigDict(from_attributes=True)
