from uuid import uuid4
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import app.models as models
from app.core.security import get_password_hash
from app.models.enums import SubscriptionStatus, PaymentStatus, UserRole
from app.services.billing import payment_method as payment_method_service
from app.services.billing import payment_service
from app.services.billing import plan_service
from app.services.billing import subscription_service
from app.services.billing import usage_service


async def _create_user(async_db: AsyncSession, prefix: str) -> models.User:
    user = models.User(
        name=f"{prefix} User",
        email=f"{prefix}_{uuid4().hex[:8]}@example.com",
        password_hash=get_password_hash("securepassword123"),
        role=UserRole.ENTREPRENEUR,
        is_active=True,
        is_verified=True,
    )
    async_db.add(user)
    await async_db.commit()
    await async_db.refresh(user)
    return user


@pytest.mark.asyncio
async def test_plan_and_subscription_services_crud_and_limit_sync(async_db: AsyncSession):
    test_user = await _create_user(async_db, "billing")
    free_plan = await plan_service.create_plan(
        async_db,
        {"name": "FREE", "price": 0.0, "features_json": {"ai_runs": 10}, "is_active": True},
    )
    pro_plan = await plan_service.create_plan(
        async_db,
        {"name": "PRO", "price": 20.0, "features_json": {"ai_runs": 100}, "is_active": True},
    )

    assert await plan_service.get_plan(async_db, free_plan.id) is not None
    plans_list = await plan_service.get_plans(async_db, skip=0, limit=10)
    assert len(plans_list) >= 2

    free_plan = await plan_service.update_plan(async_db, free_plan, {"price": 1.0})
    assert free_plan.price == 1.0

    subscription = await subscription_service.create_subscription(
        async_db,
        {"user_id": test_user.id, "plan_id": free_plan.id},
    )
    assert subscription.status == SubscriptionStatus.PENDING
    assert subscription.start_date is not None
    assert await subscription_service.get_active_subscription(async_db, test_user.id) is None

    stmt = select(models.Usage).where(models.Usage.user_id == test_user.id, models.Usage.resource_type == "AI_REQUEST")
    result = await async_db.execute(stmt)
    usage = result.scalar_one_or_none()
    assert usage is not None
    assert usage.limit_value == 10

    subscription = await subscription_service.update_subscription(
        async_db,
        subscription,
        {"status": SubscriptionStatus.ACTIVE, "plan_id": pro_plan.id},
    )
    assert subscription.status == SubscriptionStatus.ACTIVE
    assert await subscription_service.get_subscription(async_db, subscription.id) is not None
    active_sub = await subscription_service.get_active_subscription(async_db, test_user.id)
    assert active_sub is not None
    assert active_sub.id == subscription.id
    
    user_subs = await subscription_service.get_subscriptions(async_db, user_id=test_user.id)
    assert len(user_subs) == 1

    result = await async_db.execute(stmt)
    usage = result.scalar_one_or_none()
    assert usage is not None
    assert usage.limit_value == 100

    deleted_subscription = await subscription_service.delete_subscription(async_db, subscription.id)
    assert deleted_subscription is not None
    assert await subscription_service.delete_subscription(async_db, subscription.id) is None

    deleted_plan = await plan_service.delete_plan(async_db, free_plan.id)
    assert deleted_plan is not None
    assert await plan_service.delete_plan(async_db, free_plan.id) is None


@pytest.mark.asyncio
async def test_payment_method_usage_and_payment_services_paths(async_db: AsyncSession):
    test_user = await _create_user(async_db, "billing_primary")
    other_user = await _create_user(async_db, "billing_other")
    plan = await plan_service.create_plan(
        async_db,
        {"name": "PRO", "price": 20.0, "features_json": {"ai_runs": 100}, "is_active": True},
    )

    payment_method = await payment_method_service.create_payment_method(
        async_db,
        {
            "user_id": test_user.id,
            "provider": "stripe",
            "token_ref": "tok_primary",
            "last4": "4242",
            "is_default": True,
        },
    )
    payment_method_id = payment_method.id  # Cache ID early to avoid lazy loading later
    await payment_method_service.create_payment_method(
        async_db,
        {
            "user_id": other_user.id,
            "provider": "stripe",
            "token_ref": "tok_other",
            "last4": "1111",
        },
    )

    assert await payment_method_service.get_payment_method(async_db, payment_method.id) is not None
    user_pms = await payment_method_service.get_payment_methods(async_db, user_id=test_user.id)
    assert len(user_pms) == 1

    payment_method = await payment_method_service.update_payment_method(
        async_db,
        payment_method,
        {"last4": "0005"},
    )
    assert payment_method.last4 == "0005"

    usage = await usage_service.create_usage(
        async_db,
        {"user_id": test_user.id, "resource_type": "AI_REQUEST", "used": 0, "limit_value": 2},
    )
    usage = await usage_service.record_usage(async_db, test_user.id, "AI_REQUEST", quantity=2)
    assert usage.used == 2
    assert await usage_service.check_usage_limit(async_db, test_user.id, "AI_REQUEST") is False

    other_usage = await usage_service.record_usage(async_db, other_user.id, "AI_REQUEST", quantity=3)
    assert other_usage.used == 3
    assert await usage_service.check_usage_limit(async_db, other_user.id, "AI_REQUEST") is True

    usage = await usage_service.update_usage(async_db, usage, {"limit_value": 5})
    assert usage.limit_value == 5
    assert await usage_service.get_usage(async_db, usage.id) is not None
    
    usages_list = await usage_service.get_usages(async_db, user_id=test_user.id)
    assert len(usages_list) >= 1

    subscription = await subscription_service.create_subscription(
        async_db,
        {"user_id": test_user.id, "plan_id": plan.id, "status": SubscriptionStatus.PENDING},
    )
    payment = await payment_service.process_payment(
        async_db,
        subscription_id=subscription.id,
        amount=20.0,
        method_id=payment_method.id,
        currency="usd",
    )
    assert payment.status == PaymentStatus.COMPLETED

    await async_db.refresh(subscription)
    assert subscription.status == SubscriptionStatus.ACTIVE
    assert subscription.end_date is not None

    payment = await payment_service.update_payment(async_db, payment, {"status": PaymentStatus.COMPLETED})
    assert payment.status == PaymentStatus.COMPLETED
    assert await payment_service.get_payment(async_db, payment.id) is not None
    payments_list = await payment_service.get_payments(async_db, user_id=test_user.id)
    assert len(payments_list) >= 1

    wrapper_sub = await subscription_service.create_subscription(
        async_db,
        {"user_id": test_user.id, "plan_id": plan.id},
    )
    wrapped_payment = await payment_service.process_subscription_payment(
        async_db,
        subscription_id=wrapper_sub.id,
        amount=9.0,
        payment_method_id=payment_method.id,
    )
    wrapped_payment_id = wrapped_payment.id  # Cache ID before any session operations
    assert wrapped_payment.status == PaymentStatus.COMPLETED

    await payment_service.handle_payment_reversal(async_db, payment.id)
    await async_db.refresh(payment)
    await async_db.refresh(subscription)
    assert payment.status == PaymentStatus.REFUNDED
    assert subscription.status == SubscriptionStatus.CANCELED

    stmt = select(models.Usage).where(models.Usage.user_id == test_user.id)
    res = await async_db.execute(stmt)
    usage_rows = res.scalars().all()
    assert usage_rows
    assert all(row.limit_value == 0 for row in usage_rows if row.limit_value is not None)

    await payment_service.handle_payment_reversal(async_db, uuid4())

    from app.core.exceptions import ResourceNotFoundError
    with pytest.raises(ResourceNotFoundError):
        await payment_service.process_payment(
            async_db,
            subscription_id=uuid4(),
            amount=1.0,
            method_id=payment_method.id,
        )

    deleted_payment = await payment_service.delete_payment(async_db, wrapped_payment_id)
    assert deleted_payment is not None
    assert await payment_service.delete_payment(async_db, wrapped_payment_id) is None

    deleted_pm = await payment_method_service.delete_payment_method(async_db, payment_method_id)
    assert deleted_pm is not None
    assert await payment_method_service.delete_payment_method(async_db, payment_method.id) is None


@pytest.mark.asyncio
async def test_payment_method_requires_valid_provider_and_user(async_db: AsyncSession):
    """Ensure payment methods enforce provider and user_id validation."""
    from app.core.exceptions import ValidationError

    user = await _create_user(async_db, "billing_validation")

    # Missing user_id
    with pytest.raises(ValidationError):
        await payment_method_service.create_payment_method(
            async_db,
            {
                "provider": "stripe",
                "token_ref": "tok_missing_user",
                "last4": "0000",
            },
        )

    # Empty/whitespace provider
    with pytest.raises(ValidationError):
        await payment_method_service.create_payment_method(
            async_db,
            {
                "user_id": user.id,
                "provider": "   ",
                "token_ref": "tok_bad_provider",
                "last4": "0001",
            },
        )


@pytest.mark.asyncio
async def test_plan_service_billing_cycle_and_price_validation(async_db: AsyncSession):
    """Validate plan payload normalization and safety for commercial rules."""
    from app.core.exceptions import ValidationError

    # Valid aliases normalize correctly
    monthly = await plan_service.create_plan(
        async_db,
        {"name": "Monthly Plan", "price": 10, "billing_cycle": "monthly"},
    )
    assert monthly.billing_cycle == "month"

    yearly = await plan_service.create_plan(
        async_db,
        {"name": "Yearly Plan", "price": 100, "billing_cycle": "annual"},
    )
    assert yearly.billing_cycle == "year"

    # Negative price is rejected
    with pytest.raises(ValidationError):
        await plan_service.create_plan(
            async_db,
            {"name": "Bad Plan", "price": -1},
        )

    # Unsupported billing_cycle is rejected
    with pytest.raises(ValidationError):
        await plan_service.create_plan(
            async_db,
            {"name": "Weird Plan", "price": 5, "billing_cycle": "weekly"},
        )


@pytest.mark.asyncio
async def test_usage_service_quota_and_negative_values(async_db: AsyncSession):
    """Ensure usage service protects against quota overrun and invalid quantities."""
    from app.core.exceptions import ValidationError, InvalidStateError

    user = await _create_user(async_db, "usage_limits")

    # Create a usage row with a finite limit
    usage = await usage_service.create_usage(
        async_db,
        {"user_id": user.id, "resource_type": "AI_REQUEST", "used": 0, "limit_value": 3},
    )
    assert usage.limit_value == 3

    # Recording within quota succeeds
    usage = await usage_service.record_usage(async_db, user.id, "AI_REQUEST", quantity=2)
    assert usage.used == 2

    # Exceeding quota raises InvalidStateError
    with pytest.raises(InvalidStateError):
        await usage_service.record_usage(async_db, user.id, "AI_REQUEST", quantity=2)

    # Negative "used" or "limit_value" is rejected on create/update
    with pytest.raises(ValidationError):
        await usage_service.create_usage(
            async_db,
            {"user_id": user.id, "resource_type": "AI_REQUEST", "used": -1},
        )

    with pytest.raises(ValidationError):
        await usage_service.update_usage(
            async_db,
            usage,
            {"limit_value": -5},
        )


