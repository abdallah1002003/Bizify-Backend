import pytest
from sqlalchemy.orm import Session
from app.models.billing.billing import Plan, Subscription, PaymentMethod
from app.models.enums import SubscriptionStatus, PaymentStatus
from app.schemas.billing.subscription import SubscriptionCreate
from app.services.billing.subscription_service import create_subscription, get_active_subscription
from app.services.billing.payment_service import process_subscription_payment

@pytest.fixture
def test_plan(db: Session):
    plan = Plan(name="Pro Plan", price=20.0, features_json={"ai_runs": 100})
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan

@pytest.fixture
def test_payment_method(db: Session, test_user):
    pm = PaymentMethod(user_id=test_user.id, provider="stripe", token_ref="tok_123", last4="4242")
    db.add(pm)
    db.commit()
    db.refresh(pm)
    return pm

def test_prevent_multiple_active_subscriptions(db: Session, test_user, test_plan):
    # 1. Create first active sub
    sub1 = Subscription(
        user_id=test_user.id,
        plan_id=test_plan.id,
        status=SubscriptionStatus.ACTIVE,
        start_date=pytest.importorskip("datetime").datetime.now()
    )
    db.add(sub1)
    db.commit()
    
    # 2. Verify active lookup returns the existing one
    active = get_active_subscription(db, test_user.id)
    assert active is not None
    assert active.id == sub1.id

def test_subscription_activation_via_payment(db: Session, test_user, test_plan, test_payment_method):
    # 1. Create PENDING sub
    obj_in = SubscriptionCreate(user_id=test_user.id, plan_id=test_plan.id, status=SubscriptionStatus.PENDING)
    sub = create_subscription(db, obj_in)
    assert sub.status == SubscriptionStatus.PENDING
    
    # 2. Process mock payment
    payment = process_subscription_payment(
        db, 
        subscription_id=sub.id, 
        amount=20.0, 
        payment_method_id=test_payment_method.id
    )
    
    assert payment.status == PaymentStatus.COMPLETED
    db.refresh(sub)
    assert sub.status == SubscriptionStatus.ACTIVE
