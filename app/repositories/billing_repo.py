import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional

from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.models.plan import Plan
from app.models.subscription import Subscription, SubscriptionStatus
from app.repositories.base import BaseRepository


class PlanRepository(BaseRepository[Plan, Any, Any]):
    """Data-access helpers for subscription plans."""

    def get_active_plans(self, db: Session) -> List[Plan]:
        """Return all active plans."""
        return db.query(self.model).filter(self.model.is_active.is_(True)).all()

    def get_active_by_id(self, db: Session, plan_id: uuid.UUID) -> Optional[Plan]:
        """Return a single active plan by ID, or `None`."""
        return (
            db.query(self.model)
            .filter(self.model.id == plan_id, self.model.is_active.is_(True))
            .first()
        )


class PaymentRepository(BaseRepository[Payment, Any, Any]):
    """Data-access helpers for payments."""

    def get_by_user(self, db: Session, user_id: uuid.UUID) -> List[Payment]:
        """Return all payments made by a user, newest first."""
        return (
            db.query(self.model)
            .filter(self.model.user_id == user_id)
            .order_by(self.model.created_at.desc())
            .all()
        )

    def get_by_paypal_order(self, db: Session, order_id: str) -> Optional[Payment]:
        """Find a payment by its PayPal order ID."""
        return db.query(self.model).filter(self.model.paypal_order_id == order_id).first()

    def get_by_paypal_capture(self, db: Session, capture_id: str) -> Optional[Payment]:
        """Find a payment by its PayPal capture ID."""
        return (
            db.query(self.model)
            .filter(self.model.paypal_capture_id == capture_id)
            .first()
        )

    def get_by_paymob_transaction(
        self, db: Session, transaction_id: str
    ) -> Optional[Payment]:
        """Find a payment by its Paymob transaction ID."""
        return (
            db.query(self.model)
            .filter(self.model.paymob_transaction_id == transaction_id)
            .first()
        )

    def get_by_paymob_order(
        self, db: Session, paymob_order_id: str
    ) -> Optional[Payment]:
        """Find a pending payment by its Paymob order ID."""
        return (
            db.query(self.model)
            .filter(self.model.paymob_order_id == paymob_order_id)
            .first()
        )

    def create_payment(
        self,
        db: Session,
        *,
        user_id: uuid.UUID,
        subscription_id: uuid.UUID,
        amount: Decimal,
        currency: str,
        paypal_order_id: str,
        paypal_capture_id: str,
        commit: bool = True,
    ) -> Payment:
        """Create and persist a successful payment record."""
        payment = Payment(
            user_id=user_id,
            subscription_id=subscription_id,
            amount=amount,
            currency=currency,
            status="succeeded",
            paypal_order_id=paypal_order_id,
            paypal_capture_id=paypal_capture_id,
        )
        db.add(payment)
        if commit:
            db.commit()
            db.refresh(payment)
        else:
            db.flush()
        return payment

    def create_paymob_payment(
        self,
        db: Session,
        *,
        user_id: uuid.UUID,
        subscription_id: uuid.UUID,
        amount: Decimal,
        currency: str,
        paymob_order_id: str,
        status: str = "pending",
        commit: bool = True,
    ) -> Payment:
        """Create a pending Paymob payment record (transaction ID filled in via webhook)."""
        payment = Payment(
            user_id=user_id,
            subscription_id=subscription_id,
            amount=amount,
            currency=currency,
            status=status,
            paymob_order_id=paymob_order_id,
        )
        db.add(payment)
        if commit:
            db.commit()
            db.refresh(payment)
        else:
            db.flush()
        return payment


class SubscriptionRepository(BaseRepository[Subscription, Any, Any]):
    """Data-access helpers for subscriptions."""

    def get_active_by_user(self, db: Session, user_id: uuid.UUID) -> Optional[Subscription]:
        """Return the user's active subscription, if any."""
        return (
            db.query(self.model)
            .filter(
                self.model.user_id == user_id,
                self.model.status == SubscriptionStatus.ACTIVE,
            )
            .first()
        )

    def get_by_paypal_subscription(
        self,
        db: Session,
        paypal_sub_id: str,
    ) -> Optional[Subscription]:
        """Find a subscription by its PayPal subscription ID."""
        return (
            db.query(self.model)
            .filter(self.model.paypal_subscription_id == paypal_sub_id)
            .first()
        )

    def create_or_update(
        self,
        db: Session,
        *,
        user_id: uuid.UUID,
        plan_id: uuid.UUID,
        commit: bool = False,
    ) -> Subscription:
        """Create an active subscription or update the current one."""
        subscription = self.get_active_by_user(db, user_id)

        if subscription:
            subscription.plan_id = plan_id
        else:
            subscription = Subscription(
                user_id=user_id,
                plan_id=plan_id,
                status=SubscriptionStatus.ACTIVE,
                start_date=datetime.utcnow(),
            )
            db.add(subscription)

        if commit:
            db.commit()
            db.refresh(subscription)
        else:
            db.flush()

        return subscription

    def cancel(
        self,
        db: Session,
        subscription: Subscription,
        commit: bool = True,
    ) -> Subscription:
        """Mark a subscription as canceled."""
        subscription.status = SubscriptionStatus.CANCELED
        subscription.end_date = datetime.utcnow()
        db.add(subscription)
        if commit:
            db.commit()
            db.refresh(subscription)
        else:
            db.flush()
        return subscription


plan_repo = PlanRepository(Plan)
payment_repo = PaymentRepository(Payment)
subscription_repo = SubscriptionRepository(Subscription)
