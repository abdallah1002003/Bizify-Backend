"""
Payment CRUD operations and payment processing.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Payment, Usage
from app.models.enums import SubscriptionStatus
from app.services.billing import subscription_service

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
    subscription = subscription_service.get_subscription(db, id=subscription_id)
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


def process_subscription_payment(db: Session, subscription_id, amount: float, payment_method_id):
    """Backward-compatible wrapper."""
    return process_payment(
        db,
        subscription_id=subscription_id,
        amount=amount,
        method_id=payment_method_id,
    )


def handle_payment_reversal(db: Session, payment_id: UUID) -> None:
    payment = get_payment(db, id=payment_id)
    if payment is None:
        return

    payment.status = "reversed"
    if payment.subscription_id is not None:
        subscription = subscription_service.get_subscription(db, id=payment.subscription_id)
        if subscription is not None:
            subscription.status = SubscriptionStatus.CANCELED
            db.query(Usage).filter(Usage.user_id == subscription.user_id).update({"limit_value": 0})

    db.commit()
