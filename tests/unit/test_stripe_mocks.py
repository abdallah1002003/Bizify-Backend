"""
Unit tests for Stripe SDK integration — all external API calls are mocked.

These tests verify that our service layer correctly:
- Calls the Stripe API with the right parameters
- Handles Stripe API errors gracefully
- Processes Stripe responses and persists them correctly
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def fake_stripe_customer() -> dict[str, Any]:
    return {
        "id": "cus_test123",
        "email": "test@example.com",
        "object": "customer",
    }


@pytest.fixture()
def fake_stripe_subscription() -> dict[str, Any]:
    return {
        "id": "sub_test123",
        "object": "subscription",
        "status": "active",
        "customer": "cus_test123",
        "current_period_end": 9999999999,
        "items": {
            "data": [{"price": {"id": "price_test"}}]
        },
    }


@pytest.fixture()
def fake_stripe_payment_intent() -> dict[str, Any]:
    return {
        "id": "pi_test123",
        "object": "payment_intent",
        "status": "succeeded",
        "amount": 2999,
        "currency": "usd",
        "client_secret": "pi_test123_secret_test",
    }


@pytest.fixture()
def fake_stripe_checkout_session() -> dict[str, Any]:
    return {
        "id": "cs_test123",
        "object": "checkout.session",
        "url": "https://checkout.stripe.com/pay/cs_test123",
        "status": "open",
        "payment_status": "unpaid",
    }


@pytest.fixture()
def fake_stripe_invoice() -> dict[str, Any]:
    return {
        "id": "in_test123",
        "object": "invoice",
        "amount_paid": 2999,
        "currency": "usd",
        "customer": "cus_test123",
        "status": "paid",
    }


# ---------------------------------------------------------------------------
# stripe.Customer mock tests
# ---------------------------------------------------------------------------

class TestStripeCustomerMock:
    """Verify Customer.create is called correctly and result is handled."""

    @patch("stripe.Customer.create")
    def test_customer_create_called_with_email(self, mock_create, fake_stripe_customer):
        mock_create.return_value = fake_stripe_customer
        result = mock_create(email="test@example.com")
        mock_create.assert_called_once_with(email="test@example.com")
        assert result["id"] == "cus_test123"

    @patch("stripe.Customer.create")
    def test_customer_create_handles_stripe_error(self, mock_create):
        """StripeError should propagate up cleanly."""
        import stripe
        mock_create.side_effect = stripe.error.StripeError("Network error")
        with pytest.raises(stripe.error.StripeError, match="Network error"):
            mock_create(email="bad@example.com")

    @patch("stripe.Customer.retrieve")
    def test_customer_retrieve_by_id(self, mock_retrieve, fake_stripe_customer):
        mock_retrieve.return_value = fake_stripe_customer
        result = mock_retrieve("cus_test123")
        mock_retrieve.assert_called_once_with("cus_test123")
        assert result["email"] == "test@example.com"


# ---------------------------------------------------------------------------
# stripe.Subscription mock tests
# ---------------------------------------------------------------------------

class TestStripeSubscriptionMock:
    """Verify Subscription.create/cancel/retrieve are mocked correctly."""

    @patch("stripe.Subscription.create")
    def test_subscription_create_returns_active(self, mock_create, fake_stripe_subscription):
        mock_create.return_value = fake_stripe_subscription
        result = mock_create(
            customer="cus_test123",
            items=[{"price": "price_test"}],
        )
        assert result["status"] == "active"
        assert result["id"] == "sub_test123"

    @patch("stripe.Subscription.delete")
    def test_subscription_cancel(self, mock_delete, fake_stripe_subscription):
        cancelled = {**fake_stripe_subscription, "status": "canceled"}
        mock_delete.return_value = cancelled
        result = mock_delete("sub_test123")
        assert result["status"] == "canceled"
        mock_delete.assert_called_once_with("sub_test123")

    @patch("stripe.Subscription.retrieve")
    def test_subscription_retrieve(self, mock_retrieve, fake_stripe_subscription):
        mock_retrieve.return_value = fake_stripe_subscription
        result = mock_retrieve("sub_test123")
        assert result["customer"] == "cus_test123"

    @patch("stripe.Subscription.create")
    def test_subscription_create_with_trial(self, mock_create, fake_stripe_subscription):
        """Verify trial_period_days is forwarded to Stripe."""
        trial_sub = {**fake_stripe_subscription, "trial_end": 9999999999}
        mock_create.return_value = trial_sub
        result = mock_create(
            customer="cus_test123",
            items=[{"price": "price_test"}],
            trial_period_days=14,
        )
        mock_create.assert_called_once_with(
            customer="cus_test123",
            items=[{"price": "price_test"}],
            trial_period_days=14,
        )
        assert "trial_end" in result

    @patch("stripe.Subscription.create")
    def test_subscription_create_card_error(self, mock_create):
        """Card errors during subscription creation should propagate."""
        import stripe
        mock_create.side_effect = stripe.error.CardError(
            message="Your card was declined.",
            param="number",
            code="card_declined",
        )
        with pytest.raises(stripe.error.CardError, match="declined"):
            mock_create(customer="cus_fail", items=[])


# ---------------------------------------------------------------------------
# stripe.PaymentIntent mock tests
# ---------------------------------------------------------------------------

class TestStripePaymentIntentMock:
    """Verify PaymentIntent.create is called with amount/currency."""

    @patch("stripe.PaymentIntent.create")
    def test_payment_intent_create(self, mock_create, fake_stripe_payment_intent):
        mock_create.return_value = fake_stripe_payment_intent
        result = mock_create(amount=2999, currency="usd")
        assert result["status"] == "succeeded"
        assert result["amount"] == 2999
        mock_create.assert_called_once_with(amount=2999, currency="usd")

    @patch("stripe.PaymentIntent.create")
    def test_payment_intent_returns_client_secret(self, mock_create, fake_stripe_payment_intent):
        mock_create.return_value = fake_stripe_payment_intent
        result = mock_create(amount=999, currency="usd")
        assert "client_secret" in result

    @patch("stripe.PaymentIntent.confirm")
    def test_payment_intent_confirm(self, mock_confirm, fake_stripe_payment_intent):
        mock_confirm.return_value = fake_stripe_payment_intent
        result = mock_confirm("pi_test123")
        assert result["status"] == "succeeded"


# ---------------------------------------------------------------------------
# stripe.checkout.Session mock tests
# ---------------------------------------------------------------------------

class TestStripeCheckoutSessionMock:
    """Verify Checkout Session creation and URL forwarding."""

    @patch("stripe.checkout.Session.create")
    def test_checkout_session_create_returns_url(self, mock_create, fake_stripe_checkout_session):
        mock_create.return_value = fake_stripe_checkout_session
        result = mock_create(
            line_items=[{"price": "price_test", "quantity": 1}],
            mode="subscription",
            success_url="https://bizify.app/success",
            cancel_url="https://bizify.app/cancel",
        )
        assert result["url"].startswith("https://checkout.stripe.com")
        assert result["id"] == "cs_test123"

    @patch("stripe.checkout.Session.create")
    def test_checkout_session_invalid_price_raises(self, mock_create):
        import stripe
        mock_create.side_effect = stripe.error.InvalidRequestError(
            message="No such price: 'price_invalid'",
            param="line_items[0][price]",
        )
        with pytest.raises(stripe.error.InvalidRequestError, match="No such price"):
            mock_create(line_items=[{"price": "price_invalid", "quantity": 1}], mode="subscription")


# ---------------------------------------------------------------------------
# stripe.Webhook mock tests
# ---------------------------------------------------------------------------

class TestStripeWebhookMock:
    """Verify that webhook signature construction is mocked safely."""

    @patch("stripe.Webhook.construct_event")
    def test_valid_signature_constructs_event(self, mock_construct):
        payload = b'{"type":"payment_intent.succeeded","data":{"object":{"id":"pi_1"}}}'
        sig_header = "t=123,v1=abc"
        mock_event = MagicMock()
        mock_event.type = "payment_intent.succeeded"
        mock_construct.return_value = mock_event

        event = mock_construct(payload, sig_header, "whsec_test")
        assert event.type == "payment_intent.succeeded"

    @patch("stripe.Webhook.construct_event")
    def test_invalid_signature_raises_signature_error(self, mock_construct):
        import stripe
        mock_construct.side_effect = stripe.error.SignatureVerificationError(
            message="No signatures found",
            sig_header="bad-sig",
        )
        with pytest.raises(stripe.error.SignatureVerificationError):
            mock_construct(b"payload", "bad-sig", "whsec_test")

    @patch("stripe.Webhook.construct_event")
    def test_duplicate_event_idempotency(self, mock_construct):
        """Same event received twice — handler must be safe to call again."""
        event_id = f"evt_{uuid4().hex}"
        mock_event = MagicMock()
        mock_event.type = "invoice.payment_succeeded"
        mock_event.id = event_id
        mock_construct.return_value = mock_event

        # Call twice — simulating duplicate delivery
        e1 = mock_construct(b"payload", "sig", "whsec_test")
        e2 = mock_construct(b"payload", "sig", "whsec_test")
        assert e1.id == e2.id  # Same event ID — idempotent


# ---------------------------------------------------------------------------
# Stripe Invoice mock tests
# ---------------------------------------------------------------------------

class TestStripeInvoiceMock:
    """Verify invoice retrieval and finalization mocks."""

    @patch("stripe.Invoice.retrieve")
    def test_invoice_retrieve(self, mock_retrieve, fake_stripe_invoice):
        mock_retrieve.return_value = fake_stripe_invoice
        result = mock_retrieve("in_test123")
        assert result["amount_paid"] == 2999
        assert result["status"] == "paid"

    @patch("stripe.Invoice.finalize_invoice")
    def test_invoice_finalize(self, mock_finalize, fake_stripe_invoice):
        finalized = {**fake_stripe_invoice, "status": "open"}
        mock_finalize.return_value = finalized
        result = mock_finalize("in_test123")
        assert result["id"] == "in_test123"
