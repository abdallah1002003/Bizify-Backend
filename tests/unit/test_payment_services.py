# ruff: noqa
"""
Unit tests for payment services - comprehensive coverage of billing module.
"""

import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime, timezone

from decimal import Decimal
from app.models import User, Plan, Subscription
from app.models.enums import UserRole, SubscriptionStatus, PaymentStatus
<<<<<<< HEAD
from app.services.billing.payment_method import PaymentMethodService
from app.services.billing.payment_service import PaymentService
=======
from app.services.billing.payment_method import (
    get_payment_method,
    get_payment_methods,
    create_payment_method,
)
from app.services.billing.payment_service import (
    get_payment,
    get_payments,
    create_payment,
)
>>>>>>> origin/main
from app.schemas.billing.payment_method import PaymentMethodCreate
from app.core.security import get_password_hash


@pytest_asyncio.fixture
async def test_user(async_db):
    """Create a test user."""
    user = User(
        id=uuid4(),
        name="Payment Test User",
        email=f"payment-{uuid4()}@example.com",
        password_hash=get_password_hash("testpass123"),
        role=UserRole.ENTREPRENEUR,
        is_active=True,
        is_verified=True,
    )
    async_db.add(user)
    await async_db.commit()
    await async_db.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_plan(async_db):
    """Create a test plan."""
    plan = Plan(
        id=uuid4(),
        name="Pro Plan",
        price=Decimal("29.99"),
        features_json={"ai_runs": 100},
        is_active=True,
    )
    async_db.add(plan)
    await async_db.commit()
    await async_db.refresh(plan)
    return plan


@pytest_asyncio.fixture
async def test_subscription(async_db, test_user, test_plan):
    """Create a test subscription."""
    sub = Subscription(
        id=uuid4(),
        user_id=test_user.id,
        plan_id=test_plan.id,
        status=SubscriptionStatus.ACTIVE,
        start_date=datetime.now(timezone.utc),
    )
    async_db.add(sub)
    await async_db.commit()
    await async_db.refresh(sub)
    return sub


# ============================================================================
# Payment Method Tests
# ============================================================================

class TestPaymentMethodCRUD:
    """Test payment method CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_payment_method(self, async_db, test_user):
        """Test creating a payment method."""
        method_data = PaymentMethodCreate(
            user_id=test_user.id,
            provider="stripe",
            token_ref="tok_visa_123",
            last4="4242",
        )
        
<<<<<<< HEAD
        method = await PaymentMethodService(async_db).create_payment_method(method_data)
=======
        method = await create_payment_method(async_db, method_data)
>>>>>>> origin/main
        
        assert method is not None
        assert method.user_id == test_user.id
        assert method.provider == "stripe"
        assert method.last4 == "4242"

    @pytest.mark.asyncio
    async def test_get_payment_method(self, async_db, test_user):
        """Test retrieving a payment method."""
        method_data = PaymentMethodCreate(
            user_id=test_user.id,
            provider="stripe",
            token_ref="tok_123",
            last4="4242",
        )
<<<<<<< HEAD
        created = await PaymentMethodService(async_db).create_payment_method(method_data)
        
        retrieved = await PaymentMethodService(async_db).get_payment_method(created.id)
=======
        created = await create_payment_method(async_db, method_data)
        
        retrieved = await get_payment_method(async_db, created.id)
>>>>>>> origin/main
        
        assert retrieved is not None
        assert retrieved.id == created.id

    @pytest.mark.asyncio
    async def test_list_payment_methods(self, async_db, test_user):
        """Test listing payment methods for a user."""
        # Create 3 payment methods
        for i in range(3):
            method_data = PaymentMethodCreate(
                user_id=test_user.id,
                provider="stripe",
                token_ref=f"tok_{i}",
                last4=f"424{i}",
            )
<<<<<<< HEAD
            await PaymentMethodService(async_db).create_payment_method(method_data)
        
        methods = await PaymentMethodService(async_db).get_payment_methods(user_id=test_user.id)
=======
            await create_payment_method(async_db, method_data)
        
        methods = await get_payment_methods(async_db, user_id=test_user.id)
>>>>>>> origin/main
        
        assert len(methods) >= 3
        assert all(m.user_id == test_user.id for m in methods)

    @pytest.mark.asyncio
    async def test_payment_method_belongs_to_user(self, async_db, test_user):
        """Test that payment method belongs to correct user."""
        method_data = PaymentMethodCreate(
            user_id=test_user.id,
            provider="stripe",
            token_ref="tok_test",
            last4="1234",
        )
        
<<<<<<< HEAD
        method = await PaymentMethodService(async_db).create_payment_method(method_data)
=======
        method = await create_payment_method(async_db, method_data)
>>>>>>> origin/main
        
        assert method.user == test_user


# ============================================================================
# Payment Tests
# ============================================================================

class TestPaymentCRUD:
    """Test payment CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_payment(self, async_db, test_subscription, test_user):
        """Test creating a payment."""
        payment_data = {
            "user_id": test_user.id,
            "subscription_id": test_subscription.id,
            "amount": 29.99,
            "currency": "USD",
        }
        
<<<<<<< HEAD
        payment = await PaymentService(async_db).create_payment(payment_data)
=======
        payment = await create_payment(async_db, payment_data)
>>>>>>> origin/main
        
        assert payment is not None
        assert payment.amount == Decimal("29.99")
        assert payment.user_id == test_user.id
        assert payment.subscription_id == test_subscription.id
        assert payment.status == PaymentStatus.PENDING

    @pytest.mark.asyncio
    async def test_get_payment(self, async_db, test_subscription, test_user):
        """Test retrieving a payment."""
        payment_data = {
            "user_id": test_user.id,
            "subscription_id": test_subscription.id,
            "amount": Decimal("49.99"),
            "currency": "USD",
        }
<<<<<<< HEAD
        created = await PaymentService(async_db).create_payment(payment_data)
        
        retrieved = await PaymentService(async_db).get_payment(created.id)
=======
        created = await create_payment(async_db, payment_data)
        
        retrieved = await get_payment(async_db, created.id)
>>>>>>> origin/main
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.amount == Decimal("49.99")

    @pytest.mark.asyncio
    async def test_list_payments_for_user(self, async_db, test_subscription, test_user):
        """Test listing payments for a user."""
        # Create 2 payments
        for i in range(2):
            payment_data = {
                "user_id": test_user.id,
                "subscription_id": test_subscription.id,
                "amount": Decimal("29.99") + Decimal(str(i)),
                "currency": "USD",
            }
<<<<<<< HEAD
            await PaymentService(async_db).create_payment(payment_data)
        
        payments = await PaymentService(async_db).get_payments(user_id=test_user.id)
=======
            await create_payment(async_db, payment_data)
        
        payments = await get_payments(async_db, user_id=test_user.id)
>>>>>>> origin/main
        
        assert len(payments) >= 2
        assert all(p.user_id == test_user.id for p in payments)

    @pytest.mark.asyncio
    async def test_payment_default_currency_is_usd(self, async_db, test_subscription, test_user):
        """Test that payments default to USD currency."""
        payment_data = {
            "user_id": test_user.id,
            "subscription_id": test_subscription.id,
            "amount": Decimal("29.99"),
        }
        
<<<<<<< HEAD
        payment = await PaymentService(async_db).create_payment(payment_data)
=======
        payment = await create_payment(async_db, payment_data)
>>>>>>> origin/main
        
        assert payment.currency == "USD"

    @pytest.mark.asyncio
    async def test_payment_links_to_subscription(self, async_db, test_subscription, test_user):
        """Test that payment links correctly to subscription."""
        payment_data = {
            "user_id": test_user.id,
            "subscription_id": test_subscription.id,
            "amount": Decimal("29.99"),
            "currency": "USD",
        }
        
<<<<<<< HEAD
        payment = await PaymentService(async_db).create_payment(payment_data)
=======
        payment = await create_payment(async_db, payment_data)
>>>>>>> origin/main
        
        assert payment.subscription == test_subscription

    @pytest.mark.asyncio
    async def test_payment_has_timestamp(self, async_db, test_subscription, test_user):
        """Test that payments have a created_at timestamp."""
        payment_data = {
            "user_id": test_user.id,
            "subscription_id": test_subscription.id,
            "amount": Decimal("29.99"),
            "currency": "USD",
        }
        
<<<<<<< HEAD
        payment = await PaymentService(async_db).create_payment(payment_data)
=======
        payment = await create_payment(async_db, payment_data)
>>>>>>> origin/main
        
        assert payment.created_at is not None
        assert isinstance(payment.created_at, datetime)

    @pytest.mark.asyncio
    async def test_multiple_payments_same_subscription(self, async_db, test_subscription, test_user):
        """Test creating multiple payments for same subscription."""
        for i in range(3):
            payment_data = {
                "user_id": test_user.id,
                "subscription_id": test_subscription.id,
                "amount": Decimal("29.99"),
                "currency": "USD",
            }
<<<<<<< HEAD
            await PaymentService(async_db).create_payment(payment_data)
        
        payments = await PaymentService(async_db).get_payments(user_id=test_user.id)
=======
            await create_payment(async_db, payment_data)
        
        payments = await get_payments(async_db, user_id=test_user.id)
>>>>>>> origin/main
        subscription_payments = [p for p in payments if p.subscription_id == test_subscription.id]
        
        assert len(subscription_payments) == 3

    @pytest.mark.asyncio
    async def test_payment_status_enum_values(self, async_db, test_subscription, test_user):
        """Test that PaymentStatus enum has all required values."""
        assert hasattr(PaymentStatus, 'PENDING')
        assert hasattr(PaymentStatus, 'COMPLETED')
        assert hasattr(PaymentStatus, 'FAILED')
        assert hasattr(PaymentStatus, 'REFUNDED')
