"""
Subscription CRUD operations and plan synchronization.
"""
from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Subscription, Usage
from app.models.enums import SubscriptionStatus
from app.services.billing import plan_service

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


def _sync_plan_limits(db: Session, subscription: Subscription) -> None:
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

    db.commit()


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
    data = _to_update_dict(obj_in)
    data.setdefault("status", SubscriptionStatus.PENDING)
    data.setdefault("start_date", _utc_now())

    db_obj = Subscription(**data)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)

    _sync_plan_limits(db, db_obj)
    return db_obj


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
