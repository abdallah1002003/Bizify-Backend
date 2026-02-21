from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.billing import billing_service


def create_subscription(db: Session, obj_in):
    return billing_service.create_subscription(db, obj_in)


def get_active_subscription(db: Session, user_id):
    return billing_service.get_active_subscription(db, user_id)
