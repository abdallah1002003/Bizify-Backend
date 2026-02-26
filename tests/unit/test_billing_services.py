import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.billing.billing import Plan, Subscription, PaymentMethod
from app.models.enums import SubscriptionStatus, PaymentStatus
from app.schemas.billing.subscription import SubscriptionCreate
from app.services.billing.subscription_service import create_subscription, get_active_subscription
from app.services.billing.payment_service import process_subscription_payment

@pytest_asyncio.fixture
async def async_test_plan(async_db: AsyncSession):
    plan = Plan(name="Pro Plan", price=20.0, features_json={"ai_runs": 100})
    async_db.add(plan)
    await async_db.commit()
    await async_db.refresh(plan)
    return plan

@pytest_asyncio.fixture
async def async_test_payment_method(async_db: AsyncSession):
    from app.models.users.user import User
    from app.models.enums import UserRole
    from app.core.security import get_password_hash
    import uuid
    user = User(
        email=f"pay_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=get_password_hash("testpass"),
        name="Pay User",
        role=UserRole.ENTREPRENEUR,
        is_active=True,
        is_verified=True
    )
    async_db.add(user)
    await async_db.commit()
    await async_db.refresh(user)

    pm = PaymentMethod(user_id=user.id, provider="stripe", token_ref="tok_123", last4="4242")
    async_db.add(pm)
    await async_db.commit()
    await async_db.refresh(pm)
    return pm, user

@pytest.mark.asyncio
async def test_prevent_multiple_active_subscriptions(async_db: AsyncSession, async_test_plan, async_test_payment_method):
    _, test_user = async_test_payment_method
    # 1. Create first active sub
    sub1 = Subscription(
        user_id=test_user.id,
        plan_id=async_test_plan.id,
        status=SubscriptionStatus.ACTIVE,
        start_date=pytest.importorskip("datetime").datetime.now()
    )
    async_db.add(sub1)
    await async_db.commit()
    
    # 2. Verify active lookup returns the existing one
    active = await get_active_subscription(async_db, test_user.id)
    assert active is not None
    assert active.id == sub1.id

@pytest.mark.asyncio
async def test_subscription_activation_via_payment(async_db: AsyncSession, async_test_plan, async_test_payment_method):
    test_payment_method, test_user = async_test_payment_method
    # 1. Create PENDING sub
    obj_in = SubscriptionCreate(user_id=test_user.id, plan_id=async_test_plan.id, status=SubscriptionStatus.PENDING)
    sub = await create_subscription(async_db, obj_in)
    assert sub.status == SubscriptionStatus.PENDING
    
    # 2. Process mock payment
    payment = await process_subscription_payment(
        async_db, 
        subscription_id=sub.id, 
        amount=20.0, 
        payment_method_id=test_payment_method.id
    )
    
    assert payment.status == PaymentStatus.COMPLETED
    await async_db.refresh(sub)
    assert sub.status == SubscriptionStatus.ACTIVE
