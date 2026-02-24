from datetime import datetime, timezone
from uuid import uuid4

import pytest

import app.models as models
from app.core.security import get_password_hash
from app.models.enums import SubscriptionStatus, PaymentStatus, UserRole
from app.services.billing import billing_service
from app.services.billing import payment_method as payment_method_service
from app.services.billing import payment_service
from app.services.billing import plan_service
from app.services.billing import subscription_service
from app.services.billing import usage_service


def _create_user(db, prefix: str) -> models.User:
    user = models.User(
        name=f"{prefix} User",
        email=f"{prefix}_{uuid4().hex[:8]}@example.com",
        password_hash=get_password_hash("securepassword123"),
        role=UserRole.ENTREPRENEUR,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_plan_and_subscription_services_crud_and_limit_sync(db, test_user):
    free_plan = plan_service.create_plan(
        db,
        {"name": "FREE", "price": 0.0, "features_json": {"ai_runs": 10}, "is_active": True},
    )
    pro_plan = plan_service.create_plan(
        db,
        {"name": "PRO", "price": 20.0, "features_json": {"ai_runs": 100}, "is_active": True},
    )

    assert plan_service.get_plan(db, free_plan.id) is not None
    assert len(plan_service.get_plans(db, skip=0, limit=10)) >= 2

    free_plan = plan_service.update_plan(db, free_plan, {"price": 1.0})
    assert free_plan.price == 1.0

    subscription = subscription_service.create_subscription(
        db,
        {"user_id": test_user.id, "plan_id": free_plan.id},
    )
    assert subscription.status == SubscriptionStatus.PENDING
    assert subscription.start_date is not None
    assert subscription_service.get_active_subscription(db, test_user.id) is None

    usage = (
        db.query(models.Usage)
        .filter(models.Usage.user_id == test_user.id, models.Usage.resource_type == "AI_REQUEST")
        .first()
    )
    assert usage is not None
    assert usage.limit_value == 10

    subscription = subscription_service.update_subscription(
        db,
        subscription,
        {"status": SubscriptionStatus.ACTIVE, "plan_id": pro_plan.id},
    )
    assert subscription.status == SubscriptionStatus.ACTIVE
    assert subscription_service.get_subscription(db, subscription.id) is not None
    assert subscription_service.get_active_subscription(db, test_user.id).id == subscription.id
    assert len(subscription_service.get_subscriptions(db, user_id=test_user.id)) == 1

    usage = (
        db.query(models.Usage)
        .filter(models.Usage.user_id == test_user.id, models.Usage.resource_type == "AI_REQUEST")
        .first()
    )
    assert usage is not None
    assert usage.limit_value == 100

    deleted_subscription = subscription_service.delete_subscription(db, subscription.id)
    assert deleted_subscription is not None
    assert subscription_service.delete_subscription(db, subscription.id) is None

    deleted_plan = plan_service.delete_plan(db, free_plan.id)
    assert deleted_plan is not None
    assert plan_service.delete_plan(db, free_plan.id) is None


def test_payment_method_usage_and_payment_services_paths(db, test_user):
    other_user = _create_user(db, "billing_other")
    plan = plan_service.create_plan(
        db,
        {"name": "PRO", "price": 20.0, "features_json": {"ai_runs": 100}, "is_active": True},
    )

    payment_method = payment_method_service.create_payment_method(
        db,
        {
            "user_id": test_user.id,
            "provider": "stripe",
            "token_ref": "tok_primary",
            "last4": "4242",
            "is_default": True,
        },
    )
    payment_method_service.create_payment_method(
        db,
        {
            "user_id": other_user.id,
            "provider": "stripe",
            "token_ref": "tok_other",
            "last4": "1111",
        },
    )

    assert payment_method_service.get_payment_method(db, payment_method.id) is not None
    assert len(payment_method_service.get_payment_methods(db, user_id=test_user.id)) == 1

    payment_method = payment_method_service.update_payment_method(
        db,
        payment_method,
        {"last4": "0005"},
    )
    assert payment_method.last4 == "0005"

    usage = usage_service.create_usage(
        db,
        {"user_id": test_user.id, "resource_type": "AI_REQUEST", "used": 0, "limit_value": 2},
    )
    usage = usage_service.record_usage(db, test_user.id, "AI_REQUEST", quantity=2)
    assert usage.used == 2
    assert usage_service.check_usage_limit(db, test_user.id, "AI_REQUEST") is False

    other_usage = usage_service.record_usage(db, other_user.id, "AI_REQUEST", quantity=3)
    assert other_usage.used == 3
    assert usage_service.check_usage_limit(db, other_user.id, "AI_REQUEST") is True

    usage = usage_service.update_usage(db, usage, {"limit_value": 5})
    assert usage.limit_value == 5
    assert usage_service.get_usage(db, usage.id) is not None
    assert len(usage_service.get_usages(db, user_id=test_user.id)) >= 1

    subscription = subscription_service.create_subscription(
        db,
        {"user_id": test_user.id, "plan_id": plan.id, "status": SubscriptionStatus.PENDING},
    )
    payment = payment_service.process_payment(
        db,
        subscription_id=subscription.id,
        amount=20.0,
        method_id=payment_method.id,
        currency="usd",
    )
    assert payment.status == PaymentStatus.COMPLETED

    db.refresh(subscription)
    assert subscription.status == SubscriptionStatus.ACTIVE
    assert subscription.end_date is not None

    payment = payment_service.update_payment(db, payment, {"status": PaymentStatus.COMPLETED})
    assert payment.status == PaymentStatus.COMPLETED
    assert payment_service.get_payment(db, payment.id) is not None
    assert len(payment_service.get_payments(db, user_id=test_user.id)) >= 1

    wrapper_sub = subscription_service.create_subscription(
        db,
        {"user_id": test_user.id, "plan_id": plan.id},
    )
    wrapped_payment = payment_service.process_subscription_payment(
        db,
        subscription_id=wrapper_sub.id,
        amount=9.0,
        payment_method_id=payment_method.id,
    )
    assert wrapped_payment.status == PaymentStatus.COMPLETED

    payment_service.handle_payment_reversal(db, payment.id)
    db.refresh(payment)
    db.refresh(subscription)
    assert payment.status == PaymentStatus.REFUNDED
    assert subscription.status == SubscriptionStatus.CANCELED

    usage_rows = db.query(models.Usage).filter(models.Usage.user_id == test_user.id).all()
    assert usage_rows
    assert all(row.limit_value == 0 for row in usage_rows if row.limit_value is not None)

    payment_service.handle_payment_reversal(db, uuid4())

    from app.core.exceptions import ResourceNotFoundError
    with pytest.raises(ResourceNotFoundError):
        payment_service.process_payment(
            db,
            subscription_id=uuid4(),
            amount=1.0,
            method_id=payment_method.id,
        )

    deleted_payment = payment_service.delete_payment(db, wrapped_payment.id)
    assert deleted_payment is not None
    assert payment_service.delete_payment(db, wrapped_payment.id) is None

    deleted_pm = payment_method_service.delete_payment_method(db, payment_method.id)
    assert deleted_pm is not None
    assert payment_method_service.delete_payment_method(db, payment_method.id) is None

def test_billing_service_monolith_paths(db, test_user):
    other_user = _create_user(db, "billing_mono")
    plan = plan_service.create_plan(
        db,
        {"name": "ENTERPRISE", "price": 100.0, "features_json": {"ai_runs": 1000}, "is_active": True},
    )

    subscription = models.Subscription(
        user_id=test_user.id,
        plan_id=plan.id,
        status=SubscriptionStatus.ACTIVE,
        start_date=datetime.now(timezone.utc),
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    assert subscription_service.get_active_subscription(db, test_user.id).id == subscription.id

    usage = (
        db.query(models.Usage)
        .filter(models.Usage.user_id == test_user.id, models.Usage.resource_type == "AI_REQUEST")
        .first()
    )
    if usage:
        assert usage.limit_value == 1000

    payment_method = billing_service.create_payment_method(
        db,
        {
            "user_id": test_user.id,
            "provider": "stripe",
            "token_ref": "tok_billing_service",
            "last4": "7777",
        },
    )
    assert billing_service.get_payment_method(db, payment_method.id) is not None
    assert len(billing_service.get_payment_methods(db, user_id=test_user.id)) == 1

    payment_method = billing_service.update_payment_method(db, payment_method, {"last4": "1234"})
    assert payment_method.last4 == "1234"

    draft_payment = billing_service.create_payment(
        db,
        {
            "user_id": test_user.id,
            "subscription_id": subscription.id,
            "payment_method_id": payment_method.id,
            "amount": 5.0,
            "currency": "usd",
            "status": PaymentStatus.PENDING,
        },
    )
    assert billing_service.get_payment(db, draft_payment.id) is not None

    draft_payment = billing_service.update_payment(db, draft_payment, {"status": PaymentStatus.PENDING})
    assert draft_payment.status == PaymentStatus.PENDING
    assert len(billing_service.get_payments(db, user_id=test_user.id)) >= 1

    processed_payment = payment_service.process_payment(
        db,
        subscription_id=subscription.id,
        amount=100.0,
        method_id=payment_method.id,
    )
    assert processed_payment.status == PaymentStatus.COMPLETED

    payment_service.handle_payment_reversal(db, processed_payment.id)
    db.refresh(processed_payment)
    db.refresh(subscription)
    assert processed_payment.status == PaymentStatus.REFUNDED
    assert subscription.status == SubscriptionStatus.CANCELED

    payment_service.handle_payment_reversal(db, uuid4())

    from app.core.exceptions import ResourceNotFoundError
    with pytest.raises(ResourceNotFoundError):
        payment_service.process_payment(
            db,
            subscription_id=uuid4(),
            amount=1.0,
            method_id=payment_method.id,
        )

    created_usage = usage_service.create_usage(
        db,
        {"user_id": other_user.id, "resource_type": "FILE_UPLOAD", "used": 1, "limit_value": 5},
    )
    created_usage = usage_service.update_usage(db, created_usage, {"used": 3})
    assert created_usage.used == 3
    assert usage_service.get_usage(db, created_usage.id) is not None
    assert len(usage_service.get_usages(db, user_id=other_user.id)) == 1

    assert usage_service.check_usage_limit(db, other_user.id, "FILE_UPLOAD") is True
    usage_service.record_usage(db, other_user.id, "FILE_UPLOAD", quantity=2)
    assert usage_service.check_usage_limit(db, other_user.id, "FILE_UPLOAD") is False

    deleted_usage = usage_service.delete_usage(db, created_usage.id)
    assert deleted_usage is not None
    assert usage_service.delete_usage(db, created_usage.id) is None

    deleted_payment = payment_service.delete_payment(db, draft_payment.id)
    assert deleted_payment is not None
    assert payment_service.delete_payment(db, draft_payment.id) is None

    deleted_payment_method = billing_service.delete_payment_method(db, payment_method.id)
    assert deleted_payment_method is not None
    assert billing_service.delete_payment_method(db, payment_method.id) is None

    status = billing_service.get_detailed_status()
    assert status["module"] == "billing_service"
    assert status["status"] == "operational"
    billing_service.reset_internal_state()
