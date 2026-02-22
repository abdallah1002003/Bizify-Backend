"""
Subscription CRUD operations and plan synchronization.
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Subscription, Usage
from app.models.enums import SubscriptionStatus
from app.services.billing import plan_service
from app.services.billing.billing_service import _utc_now, _to_update_dict, _apply_updates

logger = logging.getLogger(__name__)


def _sync_plan_limits(db: Session, subscription: Subscription, auto_commit: bool = True) -> None:
    plan = plan_service.get_plan(db, id=subscription.plan_id)
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

    if auto_commit:
        db.commit()
    else:
        db.flush()


# ----------------------------
# Subscription
# ----------------------------

def get_subscription(db: Session, id: UUID) -> Optional[Subscription]:
    return db.query(Subscription).filter(Subscription.id == id).first()


def get_subscriptions(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
) -> List[Subscription]:
    query = db.query(Subscription)
    if user_id is not None:
        query = query.filter(Subscription.user_id == user_id)
    return query.offset(skip).limit(limit).all()


def get_active_subscription(db: Session, user_id: UUID) -> Optional[Subscription]:
    return (
        db.query(Subscription)
        .filter(Subscription.user_id == user_id, Subscription.status == SubscriptionStatus.ACTIVE)
        .first()
    )


def create_subscription(db: Session, obj_in: Any) -> Subscription:
    try:
        data = _to_update_dict(obj_in)
        data.setdefault("status", SubscriptionStatus.PENDING)
        data.setdefault("start_date", _utc_now())

        db_obj = Subscription(**data)
        db.add(db_obj)
        db.flush()

        _sync_plan_limits(db, db_obj, auto_commit=False)
        db.commit()
        db.refresh(db_obj)
        logger.info(f"Created subscription {db_obj.id} for user {db_obj.user_id}")
        return db_obj
    except Exception as e:
        db.rollback()
        logger.error(f"Transaction failed during create_subscription: {e}")
        raise


def update_subscription(db: Session, db_obj: Subscription, obj_in: Any) -> Subscription:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)

    _sync_plan_limits(db, db_obj)
    return db_obj


def delete_subscription(db: Session, id: UUID) -> Optional[Subscription]:
    db_obj = get_subscription(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj
