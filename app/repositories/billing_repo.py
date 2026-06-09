import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.models.plan import Plan
from app.models.ppf_credit import PPFCredit
from app.models.subscription import Subscription, SubscriptionStatus
from app.repositories.base import BaseRepository


class PlanRepository(BaseRepository[Plan, Any, Any]):
    """Data-access helpers for subscription plans."""

    def get_active_plans(self, db: Session) -> list[Plan]:
        """Return all active plans."""
        return db.query(self.model).filter(self.model.is_active.is_(True)).all()

    def get_active_by_id(self, db: Session, plan_id: uuid.UUID) -> Optional[Plan]:
        """Return a single active plan by ID, or `None`."""
        return (
            db.query(self.model)
            .filter(self.model.id == plan_id, self.model.is_active.is_(True))
            .first()
        )

    def get_free_plan(self, db: Session) -> Optional[Plan]:
        """Return the canonical Free plan used as the default on signup.

        Matches the active plan named exactly "Free" (case-insensitive). The
        cheapest one wins if more than one ever exists, keeping the result
        deterministic.
        """
        return (
            db.query(self.model)
            .filter(self.model.is_active.is_(True), func.lower(self.model.name) == "free")
            .order_by(self.model.price.asc())
            .first()
        )


class PaymentRepository(BaseRepository[Payment, Any, Any]):
    """Data-access helpers for payments."""

    def get_by_user(self, db: Session, user_id: uuid.UUID) -> list[Payment]:
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

    def create_pending_paypal_payment(
        self,
        db: Session,
        *,
        user_id: uuid.UUID,
        subscription_id: uuid.UUID,
        amount: Decimal,
        currency: str,
        paypal_order_id: str,
        commit: bool = True,
    ) -> Payment:
        """
        Persist a `pending` PayPal payment at order-creation time so the
        order_id is server-bound to a plan/amount. Capture reads this record
        instead of trusting any client-supplied plan_id.
        """
        payment = Payment(
            user_id=user_id,
            subscription_id=subscription_id,
            amount=amount,
            currency=currency,
            status="pending",
            paypal_order_id=paypal_order_id,
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

    def create_pending(
        self,
        db: Session,
        *,
        user_id: uuid.UUID,
        plan_id: uuid.UUID,
        commit: bool = False,
    ) -> Subscription:
        """
        Insert a new PENDING subscription for a payment that has been initiated
        but not yet confirmed. It is intentionally NOT activated here and is
        invisible to `get_active_by_user` until the payment gateway confirms
        success via webhook/capture. This prevents granting paid features before
        money is actually received.
        """
        subscription = Subscription(
            user_id=user_id,
            plan_id=plan_id,
            status=SubscriptionStatus.PENDING,
            start_date=datetime.utcnow(),
        )
        db.add(subscription)
        if commit:
            db.commit()
            db.refresh(subscription)
        else:
            db.flush()
        return subscription

    def activate(
        self,
        db: Session,
        subscription: Subscription,
        *,
        commit: bool = True,
    ) -> Subscription:
        """
        Mark a (pending) subscription ACTIVE after confirmed payment, cancelling
        any other currently-active subscription for the same user so a user only
        ever has one active subscription at a time.
        """
        others = (
            db.query(self.model)
            .filter(
                self.model.user_id == subscription.user_id,
                self.model.status == SubscriptionStatus.ACTIVE,
                self.model.id != subscription.id,
            )
            .all()
        )
        for other in others:
            other.status = SubscriptionStatus.CANCELED
            other.end_date = datetime.utcnow()
            db.add(other)

        subscription.status = SubscriptionStatus.ACTIVE
        if subscription.start_date is None:
            subscription.start_date = datetime.utcnow()
        subscription.end_date = None
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


class PPFCreditRepository(BaseRepository[PPFCredit, Any, Any]):
    """Data-access helpers for Pay-Per-Feature credit purchases."""

    def create_pending(
        self,
        db: Session,
        *,
        user_id: uuid.UUID,
        quantity: int,
        amount: Decimal,
        payment_method: str,
        payment_ref: str,
        commit: bool = True,
    ) -> PPFCredit:
        credit = PPFCredit(
            user_id=user_id,
            quantity=quantity,
            amount_paid=amount,
            payment_method=payment_method,
            payment_ref=payment_ref,
            status="pending",
        )
        db.add(credit)
        if commit:
            db.commit()
            db.refresh(credit)
        else:
            db.flush()
        return credit

    def confirm(self, db: Session, credit: PPFCredit) -> PPFCredit:
        credit.status = "succeeded"
        db.add(credit)
        db.commit()
        db.refresh(credit)
        return credit

    def get_by_payment_ref(self, db: Session, ref: str) -> Optional[PPFCredit]:
        return db.query(self.model).filter(self.model.payment_ref == ref).first()


plan_repo = PlanRepository(Plan)
payment_repo = PaymentRepository(Payment)
subscription_repo = SubscriptionRepository(Subscription)
ppf_credit_repo = PPFCreditRepository(PPFCredit)
