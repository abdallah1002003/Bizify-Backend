from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Payment, PaymentMethod, Plan, Subscription, Usage
from app.models.enums import SubscriptionStatus

from app.services.billing.plan_service import get_plan
from app.services.billing.subscription_service import get_subscription

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_update_dict(obj_in: Any) -> Dict[str, Any]:
    if obj_in is None:
        return {}
    if hasattr(obj_in, "model_dump"):
        return obj_in.model_dump(exclude_unset=True)
    return dict(obj_in)


def _apply_updates(db_obj: Any, update_data: Dict[str, Any]) -> Any:
    for field, value in update_data.items():
        if hasattr(db_obj, field):
            setattr(db_obj, field, value)
    return db_obj


# ----------------------------
# Usage enforcement
# ----------------------------

def check_usage_limit(db: Session, user_id: UUID, resource_type: str) -> bool:
    usage = (
        db.query(Usage)
        .filter(Usage.user_id == user_id, Usage.resource_type == resource_type)
        .first()
    )
    if usage is None or usage.limit_value is None:
        return True
    return usage.used < usage.limit_value


def record_usage(db: Session, user_id: UUID, resource_type: str, quantity: int = 1) -> Usage:
    usage = (
        db.query(Usage)
        .filter(Usage.user_id == user_id, Usage.resource_type == resource_type)
        .first()
    )
    if usage is None:
        usage = Usage(user_id=user_id, resource_type=resource_type, used=0)
        db.add(usage)

    usage.used += quantity
    db.commit()
    db.refresh(usage)
    return usage


# ----------------------------
# (Plan CRUD removed)
# ----------------------------
# ----------------------------
# Subscription (Partial CRUD removed)
# ----------------------------


def get_active_subscription(db: Session, user_id: UUID) -> Optional[Subscription]:
    return (
        db.query(Subscription)
        .filter(Subscription.user_id == user_id, Subscription.status == SubscriptionStatus.ACTIVE)
        .first()
    )


def _sync_plan_limits(db: Session, subscription: Subscription) -> None:
    plan = get_plan(db, id=subscription.plan_id)
    if plan is None:
        return

    level = (plan.name or "").upper()
    limit_by_plan = {
        "FREE": 10,
        "PRO": 100,
        "ENTERPRISE": 1000,
    }
    limit = limit_by_plan.get(level, 10)

    usage = (
        db.query(Usage)
        .filter(Usage.user_id == subscription.user_id, Usage.resource_type == "AI_REQUEST")
        .first()
    )
    if usage is None:
        usage = Usage(
            user_id=subscription.user_id,
            resource_type="AI_REQUEST",
            used=0,
            limit_value=limit,
        )
        db.add(usage)
    else:
        usage.limit_value = limit

    db.commit()


    db.commit()


# ----------------------------
# PaymentMethod
# ----------------------------

def get_payment_method(db: Session, id: UUID) -> Optional[PaymentMethod]:
    return db.query(PaymentMethod).filter(PaymentMethod.id == id).first()


def get_payment_methods(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
) -> List[PaymentMethod]:
    query = db.query(PaymentMethod)
    if user_id is not None:
        query = query.filter(PaymentMethod.user_id == user_id)
    return query.offset(skip).limit(limit).all()


def create_payment_method(db: Session, obj_in: Any) -> PaymentMethod:
    db_obj = PaymentMethod(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_payment_method(db: Session, db_obj: PaymentMethod, obj_in: Any) -> PaymentMethod:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_payment_method(db: Session, id: UUID) -> Optional[PaymentMethod]:
    db_obj = get_payment_method(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


# ----------------------------
# Payment
# ----------------------------

def get_payment(db: Session, id: UUID) -> Optional[Payment]:
    return db.query(Payment).filter(Payment.id == id).first()


def get_payments(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
) -> List[Payment]:
    query = db.query(Payment)
    if user_id is not None:
        query = query.filter(Payment.user_id == user_id)
    return query.offset(skip).limit(limit).all()


def create_payment(db: Session, obj_in: Any) -> Payment:
    db_obj = Payment(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_payment(db: Session, db_obj: Payment, obj_in: Any) -> Payment:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_payment(db: Session, id: UUID) -> Optional[Payment]:
    db_obj = get_payment(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


def process_payment(
    db: Session,
    subscription_id: UUID,
    amount: float,
    method_id: UUID,
    currency: str = "usd",
) -> Payment:
    subscription = get_subscription(db, id=subscription_id)
    if subscription is None:
        raise ValueError("Subscription not found")

    db_payment = Payment(
        user_id=subscription.user_id,
        subscription_id=subscription_id,
        payment_method_id=method_id,
        amount=amount,
        currency=currency,
        status="succeeded",
    )
    db.add(db_payment)

    subscription.status = SubscriptionStatus.ACTIVE
    base_end = subscription.end_date or _utc_now()
    subscription.end_date = base_end + timedelta(days=30)

    db.commit()
    db.refresh(db_payment)
    return db_payment


def handle_payment_reversal(db: Session, payment_id: UUID) -> None:
    payment = get_payment(db, id=payment_id)
    if payment is None:
        return

    payment.status = "reversed"
    if payment.subscription_id is not None:
        subscription = get_subscription(db, id=payment.subscription_id)
        if subscription is not None:
            subscription.status = SubscriptionStatus.CANCELED
            db.query(Usage).filter(Usage.user_id == subscription.user_id).update({"limit_value": 0})

    db.commit()


# ----------------------------
# Usage CRUD
# ----------------------------

def get_usage(db: Session, id: UUID) -> Optional[Usage]:
    return db.query(Usage).filter(Usage.id == id).first()


def get_usages(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
) -> List[Usage]:
    query = db.query(Usage)
    if user_id is not None:
        query = query.filter(Usage.user_id == user_id)
    return query.offset(skip).limit(limit).all()


def create_usage(db: Session, obj_in: Any) -> Usage:
    db_obj = Usage(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_usage(db: Session, db_obj: Usage, obj_in: Any) -> Usage:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_usage(db: Session, id: UUID) -> Optional[Usage]:
    db_obj = get_usage(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


def get_detailed_status() -> Dict[str, Any]:
    return {
        "module": "billing_service",
        "status": "operational",
        "timestamp": _utc_now().isoformat(),
    }


def reset_internal_state() -> None:
    logger.info("billing_service reset_internal_state called")
