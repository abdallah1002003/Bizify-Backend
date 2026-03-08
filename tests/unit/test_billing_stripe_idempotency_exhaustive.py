import pytest
import uuid
from unittest.mock import MagicMock, patch
from app.services.billing.stripe_idempotency import make_key, StripeIdempotencyClient

def test_make_key_deterministic():
    user_id = uuid.uuid4()
    sub_id = uuid.uuid4()
    pay_id = uuid.uuid4()
    
    key1 = make_key("test_op", user_id=user_id, amount_cents=100, date_str="2026-01-01")
    key2 = make_key("test_op", user_id=user_id, amount_cents=100, date_str="2026-01-01")
    
    assert key1 == key2
    assert len(key1) == 48

def test_make_key_parameter_variations():
    user_id = uuid.uuid4()
    sub_id = uuid.uuid4()
    pay_id = uuid.uuid4()
    
    # Base key
    base = make_key("op")
    
    # Different user
    assert make_key("op", user_id=user_id) != base
    
    # Different sub
    assert make_key("op", subscription_id=sub_id) != base
    
    # Different pay
    assert make_key("op", payment_id=pay_id) != base
    
    # Different amount
    assert make_key("op", amount_cents=500) != base
    
    # Extra string
    assert make_key("op", extra="foo") != base

@pytest.mark.asyncio
async def test_client_create_payment_intent():
    client = StripeIdempotencyClient()
    user_id = uuid.uuid4()
    
    # Mock stripe module
    mock_stripe = MagicMock()
    with patch("stripe.PaymentIntent.create", mock_stripe.PaymentIntent.create):
        await client.create_payment_intent(
            user_id=user_id,
            amount_cents=2000,
            currency="eur",
            metadata={"source": "test"},
            extra="retry-1"
        )
        
        mock_stripe.PaymentIntent.create.assert_called_once()
        _, kwargs = mock_stripe.PaymentIntent.create.call_args
        assert kwargs["amount"] == 2000
        assert kwargs["currency"] == "eur"
        assert kwargs["metadata"] == {"source": "test"}
        assert "idempotency_key" in kwargs
        assert len(kwargs["idempotency_key"]) == 48

@pytest.mark.asyncio
async def test_client_create_refund():
    client = StripeIdempotencyClient()
    user_id = uuid.uuid4()
    pi_id = "pi_123"
    
    mock_stripe = MagicMock()
    with patch("stripe.Refund.create", mock_stripe.Refund.create):
        # Case 1: Partial refund
        await client.create_refund(
            payment_intent_id=pi_id,
            amount_cents=500,
            user_id=user_id,
            extra="partial"
        )
        mock_stripe.Refund.create.assert_called_with(
            payment_intent=pi_id,
            amount=500,
            idempotency_key=pytest.any_str
        )
        
        # Case 2: Full refund
        await client.create_refund(payment_intent_id=pi_id)
        mock_stripe.Refund.create.assert_called_with(
            payment_intent=pi_id,
            idempotency_key=pytest.any_str
        )
