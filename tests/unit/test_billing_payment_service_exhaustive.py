import pytest
from uuid import uuid4
from decimal import Decimal
from datetime import timedelta, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.billing.payment_service import (
    PaymentService,
    get_payment_service,
    _coerce_payment_status,
    _normalize_currency,
    get_payment,
    get_payments,
    create_payment,
    update_payment,
    delete_payment,
    process_payment,
    process_subscription_payment,
    handle_payment_reversal,
)
from app.models import Payment, PaymentMethod, Subscription
from app.models.enums import PaymentStatus, SubscriptionStatus
from app.core.exceptions import (
    ResourceNotFoundError,
    ValidationError,
    InvalidStateError,
    DatabaseError
)

@pytest.fixture
def mock_repos():
    with patch("app.repositories.billing_repository.PaymentRepository") as p_repo, \
         patch("app.repositories.billing_repository.PaymentMethodRepository") as m_repo, \
         patch("app.repositories.billing_repository.SubscriptionRepository") as s_repo:
        yield p_repo, m_repo, s_repo

@pytest.fixture
def payment_service(mock_repos):
    db = AsyncMock()
    return PaymentService(db)

def test_coerce_status():
    assert _coerce_payment_status("completed") == PaymentStatus.COMPLETED
    assert _coerce_payment_status(PaymentStatus.PENDING) == PaymentStatus.PENDING
    with pytest.raises(ValidationError): _coerce_payment_status("invalid")

def test_normalize_currency_util():
    assert _normalize_currency(" eur ") == "EUR"
    assert _normalize_currency(None) == "USD"
    with pytest.raises(ValidationError): _normalize_currency("US")

@pytest.mark.asyncio
async def test_svc_get_delete(payment_service):
    pid = uuid4()
    payment_service.payment_repo.get = AsyncMock(); await payment_service.get_payment(pid)
    payment_service.payment_repo.get_all_filtered = AsyncMock(); await payment_service.get_payments()
    payment_service.payment_repo.delete = AsyncMock(); await payment_service.delete_payment(pid)

@pytest.mark.asyncio
async def test_svc_create_validation(payment_service):
    with pytest.raises(ValidationError): await payment_service.create_payment({"amount": "X"})
    with pytest.raises(ValidationError): await payment_service.create_payment({"amount": 0})
    with pytest.raises(ValidationError): await payment_service.create_payment({"currency": "usd"}) # Line 83 hit, 86 raises

@pytest.mark.asyncio
async def test_svc_create_checks(payment_service):
    uid, sid, mid = uuid4(), uuid4(), uuid4()
    # Missing sub
    payment_service.sub_repo.get = AsyncMock(return_value=None)
    with pytest.raises(ResourceNotFoundError): await payment_service.create_payment({"amount": 10, "subscription_id": sid})
    # Owner mismatch sub
    sub = MagicMock(spec=Subscription); sub.user_id = uuid4()
    payment_service.sub_repo.get = AsyncMock(return_value=sub)
    with pytest.raises(ValidationError): await payment_service.create_payment({"amount": 10, "subscription_id": sid, "user_id": uid})
    # Missing method
    sub.user_id = uid
    payment_service.method_repo.get = AsyncMock(return_value=None)
    with pytest.raises(ResourceNotFoundError): await payment_service.create_payment({"amount": 10, "subscription_id": sid, "user_id": uid, "payment_method_id": mid})
    # Owner mismatch method
    method = MagicMock(spec=PaymentMethod); method.user_id = uuid4()
    payment_service.method_repo.get = AsyncMock(return_value=method)
    with pytest.raises(ValidationError): await payment_service.create_payment({"amount": 10, "subscription_id": sid, "user_id": uid, "payment_method_id": mid})
    # Success
    method.user_id = uid
    payment_service.payment_repo.create = AsyncMock()
    await payment_service.create_payment({"amount": 10, "subscription_id": sid, "user_id": uid, "payment_method_id": mid, "status": "pending"})

@pytest.mark.asyncio
async def test_svc_update_checks(payment_service):
    obj = MagicMock(spec=Payment); obj.status = PaymentStatus.PENDING
    payment_service.payment_repo.update = AsyncMock()
    await payment_service.update_payment(obj, {"amount": 5, "currency": "eur", "status": "completed"})
    with pytest.raises(ValidationError): await payment_service.update_payment(obj, {"amount": "X"})
    with pytest.raises(ValidationError): await payment_service.update_payment(obj, {"amount": -1})
    obj.status = PaymentStatus.FAILED
    with pytest.raises(InvalidStateError): await payment_service.update_payment(obj, {"status": "pending"})

@pytest.mark.asyncio
async def test_svc_process_checks(payment_service):
    sid, mid, uid = uuid4(), uuid4(), uuid4()
    with pytest.raises(ValidationError): await payment_service.process_payment(sid, 0, mid)
    payment_service.sub_repo.get = AsyncMock(return_value=None)
    with pytest.raises(ResourceNotFoundError): await payment_service.process_payment(sid, 10, mid)
    sub = MagicMock(spec=Subscription); sub.status = SubscriptionStatus.CANCELED; sub.user_id = uid; sub.end_date = None
    payment_service.sub_repo.get = AsyncMock(return_value=sub)
    with pytest.raises(InvalidStateError): await payment_service.process_payment(sid, 10, mid)
    sub.status = SubscriptionStatus.ACTIVE
    payment_service.method_repo.get = AsyncMock(return_value=None)
    with pytest.raises(ResourceNotFoundError): await payment_service.process_payment(sid, 10, mid)
    method = MagicMock(spec=PaymentMethod); method.user_id = uuid4()
    payment_service.method_repo.get = AsyncMock(return_value=method)
    with pytest.raises(ValidationError): await payment_service.process_payment(sid, 10, mid)
    # Success
    method.user_id = uid
    payment_service.payment_repo.create = AsyncMock()
    await payment_service.process_payment(sid, 10, mid)
    # Error branch
    payment_service.db.commit = AsyncMock(side_effect=Exception("X"))
    with pytest.raises(DatabaseError): await payment_service.process_payment(sid, 10, mid)

@pytest.mark.asyncio
async def test_svc_reversal(payment_service):
    pid = uuid4()
    payment_service.payment_repo.get = AsyncMock(return_value=None)
    await payment_service.handle_payment_reversal(pid)
    payment = MagicMock(); payment.subscription_id = uuid4()
    sub = MagicMock(); sub.user_id = uuid4()
    payment_service.payment_repo.get = AsyncMock(return_value=payment)
    payment_service.sub_repo.get = AsyncMock(return_value=sub)
    await payment_service.handle_payment_reversal(pid)
    payment_service.db.commit = AsyncMock(side_effect=Exception("X"))
    with pytest.raises(Exception): await payment_service.handle_payment_reversal(pid)

@pytest.mark.asyncio
async def test_std_read():
    db = AsyncMock(); pid = uuid4()
    db.get = AsyncMock(); await get_payment(db, pid)
    res = MagicMock(); res.scalars().all.return_value = []
    db.execute = AsyncMock(return_value=res); await get_payments(db, user_id=uuid4(), status=PaymentStatus.COMPLETED)

@pytest.mark.asyncio
async def test_std_create_exhaustive():
    db = AsyncMock(); uid, pid = uuid4(), uuid4()
    with pytest.raises(ValidationError): await create_payment(db, {"amount": "BAD"})
    with pytest.raises(ValidationError): await create_payment(db, {"amount": 0})
    with pytest.raises(ValidationError): await create_payment(db, {"currency": "usd"})
    
    db.get = AsyncMock(return_value=None)
    with pytest.raises(ResourceNotFoundError): await create_payment(db, {"amount": 10, "subscription_id": pid})
    
    sub = MagicMock(spec=Subscription); sub.user_id = uid
    db.get = AsyncMock(return_value=sub)
    with pytest.raises(ValidationError): await create_payment(db, {"amount": 10, "subscription_id": pid, "user_id": uuid4()})
    
    db.get = AsyncMock(side_effect=[sub, None]) 
    with pytest.raises(ResourceNotFoundError): await create_payment(db, {"amount": 10, "subscription_id": pid, "payment_method_id": pid})
    
    method = MagicMock(spec=PaymentMethod); method.user_id = uuid4()
    db.get = AsyncMock(side_effect=[sub, method])
    with pytest.raises(ValidationError): await create_payment(db, {"amount": 10, "subscription_id": pid, "payment_method_id": pid, "user_id": uid})
    
    db.get = AsyncMock(return_value=sub); db.refresh = AsyncMock()
    await create_payment(db, {"amount": 10, "user_id": uid, "status": "pending"})

@pytest.mark.asyncio
async def test_std_update_delete():
    db = AsyncMock(); pid = uuid4()
    obj = MagicMock(spec=Payment); obj.status = PaymentStatus.PENDING; obj.id = pid
    # Update errors
    with pytest.raises(ValidationError): await update_payment(db, obj, {"amount": 0})
    # Line 419-420: Trigger decimal conversion error
    with pytest.raises(ValidationError): await update_payment(db, obj, {"amount": "INVALID_DECIMAL"})
    
    await update_payment(db, obj, {"amount": 5, "currency": "eur", "status": "completed"})
    # Line 436: Trigger invalid status transition
    obj.status = PaymentStatus.FAILED
    with pytest.raises(InvalidStateError): await update_payment(db, obj, {"status": "pending"})
    # Update success path
    obj.status = PaymentStatus.PENDING
    await update_payment(db, obj, {"amount": 5})
    
    # Delete paths
    db.get = AsyncMock(return_value=None); await delete_payment(db, pid)
    db.get = AsyncMock(return_value=obj); await delete_payment(db, pid)

@pytest.mark.asyncio
async def test_std_process_exhaustive():
    db = AsyncMock(); pid, uid = uuid4(), uuid4()
    with pytest.raises(ValidationError): await process_payment(db, pid, 0, pid)
    with patch("app.services.billing.subscription_service.get_subscription", return_value=None):
        with pytest.raises(ResourceNotFoundError): await process_payment(db, pid, 10, pid)
    
    sub = MagicMock(spec=Subscription); sub.status = SubscriptionStatus.CANCELED; sub.user_id = uid; sub.end_date = None
    with patch("app.services.billing.subscription_service.get_subscription", return_value=sub):
        with pytest.raises(InvalidStateError): await process_payment(db, pid, 10, pid)
        sub.status = SubscriptionStatus.ACTIVE
        db.get = AsyncMock(return_value=None) # method not found
        with pytest.raises(ResourceNotFoundError): await process_payment(db, pid, 10, pid)
        method = MagicMock(spec=PaymentMethod); method.user_id = uuid4()
        db.get = AsyncMock(return_value=method)
        with pytest.raises(ValidationError): await process_payment(db, pid, 10, pid)
        method.user_id = uid
        db.refresh = AsyncMock()
        await process_payment(db, pid, 10, pid)
        db.commit = AsyncMock(side_effect=Exception("X"))
        with pytest.raises(DatabaseError): await process_payment(db, pid, 10, pid)

@pytest.mark.asyncio
async def test_std_reversal_exhaustive():
    db = AsyncMock(); pid = uuid4()
    # Payment not found
    with patch("app.services.billing.payment_service.get_payment", return_value=None):
        await handle_payment_reversal(db, pid)
    
    # Success with sub
    payment = MagicMock(); payment.subscription_id = pid
    sub = MagicMock(); sub.user_id = uuid4()
    with patch("app.services.billing.payment_service.get_payment", return_value=payment):
        with patch("app.services.billing.subscription_service.get_subscription", return_value=sub):
            db.execute = AsyncMock()
            await handle_payment_reversal(db, pid)
            # Exception
            db.commit = AsyncMock(side_effect=Exception("X"))
            with pytest.raises(Exception): await handle_payment_reversal(db, pid)

@pytest.mark.asyncio
async def test_misc():
    db = AsyncMock(); pid = uuid4()
    assert get_payment_service(db)
    with patch("app.services.billing.payment_service.process_payment", AsyncMock()):
        await process_subscription_payment(db, pid, 10, pid)
    import app.services.billing
    assert app.services.billing.__doc__
