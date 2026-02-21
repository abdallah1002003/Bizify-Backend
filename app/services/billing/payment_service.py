from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.billing import billing_service


def process_subscription_payment(db: Session, subscription_id, amount: float, payment_method_id):
    return billing_service.process_payment(
        db,
        subscription_id=subscription_id,
        amount=amount,
        method_id=payment_method_id,
    )
