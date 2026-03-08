"""Tests covering Billing services and Stripe webhooks to close coverage gaps."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import uuid

from app.models.enums import PaymentStatus, SubscriptionStatus
from app.services.billing.payment_method import PaymentMethodService, _normalize_provider
from app.services.billing.stripe_webhook_service import StripeWebhookService
from app.core.exceptions import ValidationError

# ── PaymentMethodService ───────────────────────────────────────────────────────

def test_normalize_provider():
    with pytest.raises(ValidationError):
        _normalize_provider(None)
    with pytest.raises(ValidationError):
        _normalize_provider("")
    with pytest.raises(ValidationError):
        _normalize_provider("   ")
    assert _normalize_provider(" Stripe ") == "stripe"


@pytest.mark.asyncio
async def test_payment_method_service_exhaustive():
    db = AsyncMock()
    svc = PaymentMethodService(db)
    svc.repo = AsyncMock()
    uid = uuid.uuid4()
    user_id = uuid.uuid4()

    from app.models import PaymentMethod

    # update_payment_method: update provider, update is_default to False
    db_obj = PaymentMethod(id=uid, user_id=user_id, is_default=True)
    updated_obj = PaymentMethod(id=uid, user_id=user_id, is_default=False)
    svc.repo.update.return_value = updated_obj
    
    first_method = PaymentMethod(id=uid, user_id=user_id, is_default=False)
    with patch.object(svc.repo, "get_first_for_user", return_value=first_method):
        # We change is_default to False. It's the first method, so it should be forced back to True
        updated_obj2 = PaymentMethod(id=uid, user_id=user_id, is_default=True)
        svc.repo.update.side_effect = [updated_obj, updated_obj2] # First for initial update, second for force True
        
        await svc.update_payment_method(db_obj, {"provider": "paypal", "is_default": False})
        # Check it forced it back to True
        assert svc.repo.update.call_count == 2
        svc.repo.update.side_effect = None

    # update_payment_method: changed to true -> unsets others
    updated_true = PaymentMethod(id=uid, user_id=user_id, is_default=True)
    svc.repo.update.return_value = updated_true
    with patch.object(svc, "_unset_other_defaults", new_callable=AsyncMock) as m_unset:
        await svc.update_payment_method(db_obj, {"is_default": True})
        m_unset.assert_called_with(user_id, uid)

    # delete_payment_method: not found
    svc.repo.get.return_value = None
    assert await svc.delete_payment_method(uid) is None

    # delete_payment_method: found, was_default=True -> sets another to default
    db_obj.is_default = True
    
    svc.repo.get.return_value = db_obj
    replacement = PaymentMethod(id=uuid.uuid4(), user_id=user_id, is_default=False)
    
    with patch.object(svc.repo, "get_first_for_user", return_value=replacement):
        await svc.delete_payment_method(uid)
        svc.repo.delete.assert_called_with(uid)
        # Should have updated replacement
        svc.repo.update.assert_called_with(replacement, {"is_default": True})

    # delete_payment_method: was default but no replacement available
    with patch.object(svc.repo, "get_first_for_user", return_value=None):
        await svc.delete_payment_method(uid)
        svc.repo.delete.assert_called_with(uid)


# ── StripeWebhookService ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_stripe_webhook_service_exhaustive():
    db = AsyncMock()
    svc = StripeWebhookService(db)
    svc.payment_repo = AsyncMock()
    svc.sub_repo = AsyncMock()
    svc.user_repo = AsyncMock()
    svc.event_repo = AsyncMock()
    
    # handle_payment_intent_succeeded
    svc.payment_repo.get_pending_by_payment_intent.return_value = None
    await svc.handle_payment_intent_succeeded({"id": "pi_123"})
    
    mock_payment = MagicMock(id=uuid.uuid4())
    svc.payment_repo.get_pending_by_payment_intent.return_value = mock_payment
    await svc.handle_payment_intent_succeeded({"id": "pi_123"})
    svc.payment_repo.update.assert_called_with(mock_payment, {"status": PaymentStatus.COMPLETED}, auto_commit=False)
    
    # handle_payment_intent_failed
    svc.payment_repo.get_pending_by_payment_intent.return_value = None
    await svc.handle_payment_intent_failed({"id": "pi_123"})
    
    svc.payment_repo.get_pending_by_payment_intent.return_value = mock_payment
    await svc.handle_payment_intent_failed({"id": "pi_123"})
    svc.payment_repo.update.assert_called_with(mock_payment, {"status": PaymentStatus.FAILED}, auto_commit=False)

    # handle_subscription_deleted
    svc.sub_repo.get_by_stripe_id.return_value = None
    await svc.handle_subscription_deleted({"id": "sub_123"})
    
    mock_sub = MagicMock(id=uuid.uuid4())
    svc.sub_repo.get_by_stripe_id.return_value = mock_sub
    await svc.handle_subscription_deleted({"id": "sub_123"})
    svc.sub_repo.update.assert_called_with(mock_sub, {"status": SubscriptionStatus.CANCELED}, auto_commit=False)

    # handle_subscription_updated
    svc.sub_repo.get_by_stripe_id.return_value = None
    await svc.handle_subscription_updated({"id": "sub_123"})
    
    svc.sub_repo.get_by_stripe_id.return_value = mock_sub
    await svc.handle_subscription_updated({
        "id": "sub_123", 
        "status": "active", 
        "current_period_end": 1700000000
    })
    svc.sub_repo.update.assert_called()

    # handle_invoice_payment_succeeded
    svc.user_repo.get_by_stripe_customer_id.return_value = None
    await svc.handle_invoice_payment_succeeded({"id": "in_123", "amount_paid": 500})
    
    svc.user_repo.get_by_stripe_customer_id.return_value = MagicMock(id=uuid.uuid4())
    await svc.handle_invoice_payment_succeeded({"id": "in_123", "amount_paid": 500, "customer": "cus_123"})

    # handle_checkout_session_completed
    # missing metadata
    await svc.handle_checkout_session_completed({"id": "cs_123"})
    
    # existing sub
    svc.sub_repo.get_by_stripe_id.return_value = mock_sub
    await svc.handle_checkout_session_completed({
        "id": "cs_123", "subscription": "sub_123",
        "metadata": {"user_id": str(uuid.uuid4()), "plan_id": str(uuid.uuid4())}
    })
    
    # new sub
    svc.sub_repo.get_by_stripe_id.return_value = None
    await svc.handle_checkout_session_completed({
        "id": "cs_123", "subscription": "sub_123", "payment_status": "paid",
        "metadata": {"user_id": str(uuid.uuid4()), "plan_id": str(uuid.uuid4())}
    })
    svc.sub_repo.create.assert_called()

    # ── Dispatcher ── 
    
    # unhandled event
    assert await svc.dispatch({"type": "unknown_event"}) is False
    
    # Missing event payload id
    evt_no_id = {"type": "payment_intent.succeeded", "data": {"object": {"id": "pi_123"}}}
    svc.payment_repo.get_pending_by_payment_intent.return_value = mock_payment
    assert await svc.dispatch(evt_no_id) is True
    
    # Existing event (idempotency hit)
    svc.event_repo.get_by_event_id.return_value = MagicMock()
    assert await svc.dispatch({"type": "payment_intent.succeeded", "id": "evt_123"}) is True
    
    # Create safe returns None (concurrent insert hit constraint)
    svc.event_repo.get_by_event_id.return_value = None
    svc.event_repo.create_safe.return_value = None
    assert await svc.dispatch({"type": "payment_intent.succeeded", "id": "evt_123"}) is True

    # Error inside handler
    svc.event_repo.create_safe.return_value = MagicMock()
    with patch.object(svc, "handle_payment_intent_succeeded", new_callable=AsyncMock, side_effect=Exception("dispatch fail")):
        with pytest.raises(Exception, match="dispatch fail"):
            await svc.dispatch({"type": "payment_intent.succeeded", "id": "evt_123"})
        svc.event_repo.rollback.assert_called_once()
