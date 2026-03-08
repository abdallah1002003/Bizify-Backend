import pytest
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.billing.stripe_webhook_service import StripeWebhookService
from app.models.enums import PaymentStatus, SubscriptionStatus

@pytest.fixture
def mock_repos():
    with patch("app.repositories.billing_repository.PaymentRepository") as p_repo, \
         patch("app.repositories.billing_repository.SubscriptionRepository") as s_repo, \
         patch("app.repositories.user_repository.UserRepository") as u_repo, \
         patch("app.repositories.billing_repository.StripeWebhookRepository") as w_repo:
        yield p_repo, s_repo, u_repo, w_repo

@pytest.fixture
def webhook_service(mock_repos):
    db = AsyncMock()
    svc = StripeWebhookService(db)
    # Ensure all repo methods called with await are AsyncMocks
    svc.event_repo.commit = AsyncMock()
    svc.event_repo.rollback = AsyncMock()
    svc.event_repo.get = AsyncMock()
    svc.event_repo.create = AsyncMock()
    svc.payment_repo.update = AsyncMock()
    svc.payment_repo.get_pending_by_payment_intent = AsyncMock()
    svc.sub_repo.update = AsyncMock()
    svc.sub_repo.get_by_stripe_id = AsyncMock()
    svc.sub_repo.create = AsyncMock()
    svc.user_repo.get_by_stripe_customer_id = AsyncMock()
    return svc

@pytest.mark.asyncio
async def test_dispatch_unhandled_type(webhook_service):
    event = {"type": "unknown.event", "id": "evt_123"}
    result = await webhook_service.dispatch(event)
    assert result is False

@pytest.mark.asyncio
async def test_dispatch_idempotency_existing(webhook_service):
    event = {"type": "payment_intent.succeeded", "id": "evt_123"}
    webhook_service.event_repo.get = AsyncMock(return_value=MagicMock())
    result = await webhook_service.dispatch(event)
    assert result is True
    webhook_service.event_repo.get.assert_called_once_with("evt_123")

@pytest.mark.asyncio
async def test_dispatch_idempotency_race_condition(webhook_service):
    event = {"type": "payment_intent.succeeded", "id": "evt_123"}
    webhook_service.event_repo.get = AsyncMock(return_value=None)
    webhook_service.event_repo.create = AsyncMock(side_effect=Exception("Constraint fail"))
    result = await webhook_service.dispatch(event)
    assert result is True

@pytest.mark.asyncio
async def test_dispatch_success_and_error(webhook_service):
    event = {"type": "payment_intent.succeeded", "id": "evt_123", "data": {"object": {"id": "pi_123"}}}
    webhook_service.event_repo.get = AsyncMock(return_value=None)
    webhook_service.event_repo.create = AsyncMock()
    webhook_service.handle_payment_intent_succeeded = AsyncMock()
    
    # Success
    result = await webhook_service.dispatch(event)
    assert result is True
    webhook_service.event_repo.commit.assert_called()

    # Error
    webhook_service.handle_payment_intent_succeeded = AsyncMock(side_effect=Exception("Handler fail"))
    with pytest.raises(Exception):
        await webhook_service.dispatch(event)
    webhook_service.event_repo.rollback.assert_called()

@pytest.mark.asyncio
async def test_handle_payment_intent_succeeded(webhook_service):
    data = {"id": "pi_123"}
    mock_pm = MagicMock()
    webhook_service.payment_repo.get_pending_by_payment_intent = AsyncMock(return_value=mock_pm)
    webhook_service.payment_repo.update = AsyncMock()
    
    await webhook_service.handle_payment_intent_succeeded(data)
    webhook_service.payment_repo.update.assert_called_with(mock_pm, {"status": PaymentStatus.COMPLETED}, auto_commit=False)

@pytest.mark.asyncio
async def test_handle_payment_intent_failed(webhook_service):
    data = {"id": "pi_123"}
    mock_pm = MagicMock()
    webhook_service.payment_repo.get_pending_by_payment_intent = AsyncMock(return_value=mock_pm)
    webhook_service.payment_repo.update = AsyncMock()
    
    await webhook_service.handle_payment_intent_failed(data)
    webhook_service.payment_repo.update.assert_called_with(mock_pm, {"status": PaymentStatus.FAILED}, auto_commit=False)

@pytest.mark.asyncio
async def test_handle_subscription_deleted(webhook_service):
    data = {"id": "sub_123"}
    mock_sub = MagicMock()
    webhook_service.sub_repo.get_by_stripe_id = AsyncMock(return_value=mock_sub)
    webhook_service.sub_repo.update = AsyncMock()
    
    await webhook_service.handle_subscription_deleted(data)
    webhook_service.sub_repo.update.assert_called_with(mock_sub, {"status": SubscriptionStatus.CANCELED}, auto_commit=False)

@pytest.mark.asyncio
async def test_handle_subscription_updated(webhook_service):
    data = {
        "id": "sub_123",
        "status": "past_due",
        "current_period_end": 1735689600 # 2025-01-01
    }
    mock_sub = MagicMock()
    webhook_service.sub_repo.get_by_stripe_id = AsyncMock(return_value=mock_sub)
    webhook_service.sub_repo.update = AsyncMock()
    
    await webhook_service.handle_subscription_updated(data)
    args, _ = webhook_service.sub_repo.update.call_args
    assert args[1]["status"] == SubscriptionStatus.EXPIRED
    assert isinstance(args[1]["end_date"], datetime)

    # Not found case
    webhook_service.sub_repo.get_by_stripe_id = AsyncMock(return_value=None)
    await webhook_service.handle_subscription_updated(data)

@pytest.mark.asyncio
async def test_handle_invoice_payment_succeeded(webhook_service):
    data = {"customer": "cus_123"}
    webhook_service.user_repo.get_by_stripe_customer_id = AsyncMock(return_value=MagicMock())
    await webhook_service.handle_invoice_payment_succeeded(data)
    webhook_service.user_repo.get_by_stripe_customer_id.assert_called_with("cus_123")

@pytest.mark.asyncio
async def test_handle_checkout_session_completed(webhook_service):
    data = {
        "subscription": "sub_123",
        "payment_status": "paid",
        "metadata": {"user_id": str(uuid4()), "plan_id": str(uuid4())}
    }
    
    # Existing case
    webhook_service.sub_repo.get_by_stripe_id = AsyncMock(return_value=MagicMock())
    await webhook_service.handle_checkout_session_completed(data)
    
    # New creation case
    webhook_service.sub_repo.get_by_stripe_id = AsyncMock(return_value=None)
    webhook_service.sub_repo.create = AsyncMock()
    await webhook_service.handle_checkout_session_completed(data)
    webhook_service.sub_repo.create.assert_called()

    # Missing metadata
    await webhook_service.handle_checkout_session_completed({"metadata": {}})

@pytest.mark.asyncio
async def test_handle_event_alias(webhook_service):
    with patch.object(webhook_service, "dispatch", AsyncMock()) as mock_dispatch:
        await webhook_service.handle_event({"foo": "bar"})
        mock_dispatch.assert_called_with({"foo": "bar"})
