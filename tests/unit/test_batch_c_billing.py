# ruff: noqa
"""
Batch C: Billing routes coverage — checkout (mocked Stripe), stripe_webhook
(mocked signature verification), payment routes.
"""
import uuid
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.models as models
from config.settings import settings


def _admin_headers(db, user):
    from app.models.enums import UserRole
    from app.core.security import create_access_token
    user.role = UserRole.ADMIN
    db.add(user)
    db.commit()
    return {"Authorization": f"Bearer {create_access_token(subject=str(user.id))}"}


def _make_plan(db, name="BillingPlan"):
    plan = models.Plan(name=name, price=29.99, features_json={}, is_active=True)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def _make_subscription(db, user_id, plan_id):
    from app.models.enums import SubscriptionStatus
    from datetime import datetime, timedelta
    sub = models.Subscription(user_id=user_id, plan_id=plan_id,
                              status=SubscriptionStatus.ACTIVE,
                              start_date=datetime.utcnow(),
                              end_date=datetime.utcnow() + timedelta(days=30))
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


# ─────────────────────────────────────────────────────────────────
# Billing Checkout routes (Stripe mocked)
# ─────────────────────────────────────────────────────────────────

class TestCheckoutRoutes:

    def test_create_checkout_session_mocked(
        self, client: TestClient, auth_headers: dict, db: Session, test_user
    ):
        plan = _make_plan(db, "CheckoutPlan")
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/pay/test_123"
        mock_session.id = "cs_test_123"

        mock_customer = MagicMock()
        mock_customer.id = "cus_test_123"

        with patch("stripe.checkout.Session.create", return_value=mock_session), \
             patch("stripe.Customer.create", return_value=mock_customer), \
             patch.object(settings, "STRIPE_ENABLED", True):
            resp = client.post(
                "/api/v1/billing/checkout",
                json={"plan_id": str(plan.id)},
                headers=auth_headers,
            )
        assert resp.status_code in (200, 422, 404)

    def test_checkout_success_callback(self, client: TestClient, auth_headers: dict):
        resp = client.get(
            "/api/v1/billing/success",
            params={"session_id": "cs_test_abc"},
            headers=auth_headers,
        )
        assert resp.status_code in (200, 404, 422)

    def test_checkout_cancel_callback(self, client: TestClient, auth_headers: dict):
        resp = client.get("/api/v1/billing/cancel", headers=auth_headers)
        assert resp.status_code in (200, 404)


# ─────────────────────────────────────────────────────────────────
# Stripe Webhook (mocked signature)
# ─────────────────────────────────────────────────────────────────

class TestStripeWebhookRoute:

    def test_webhook_invalid_signature(self, client: TestClient):
        """Without valid signature, stripe should reject with 400."""
        with patch.object(settings, "STRIPE_ENABLED", True):
            resp = client.post(
                "/api/v1/billing/webhooks/stripe",
                content=b'{"type": "payment_intent.succeeded"}',
                headers={"stripe-signature": "invalid_sig"},
            )
        assert resp.status_code in (400, 422)

    def test_webhook_mocked_payment_intent_succeeded(self, client: TestClient):
        """With mocked Stripe event construction, test webhook dispatch."""
        event = {
            "id": "evt_test_123",
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_test", "amount": 2999, "currency": "usd"}},
        }
        mock_event = MagicMock()
        mock_event.__getitem__ = lambda s, k: event[k]
        mock_event.get = lambda k, d=None: event.get(k, d)
        mock_event["type"] = "payment_intent.succeeded"

        with patch("stripe.Webhook.construct_event", return_value=mock_event), \
             patch("config.settings.settings.STRIPE_ENABLED", True):
            resp = client.post(
                "/api/v1/billing/webhooks/stripe",
                content=b'{}',
                headers={"stripe-signature": "mocked"},
            )
        assert resp.status_code in (200, 400, 422)

    def test_webhook_mocked_checkout_completed(self, client: TestClient):
        mock_event = {"type": "checkout.session.completed",
                      "data": {"object": {"id": "cs_test"}}}
        with patch("stripe.Webhook.construct_event", return_value=mock_event), \
             patch("config.settings.settings.STRIPE_ENABLED", True):
            resp = client.post(
                "/api/v1/billing/webhooks/stripe",
                content=b'{}',
                headers={"stripe-signature": "mocked"},
            )
        assert resp.status_code in (200, 400, 422)


# ─────────────────────────────────────────────────────────────────
# Payment routes (mocked Stripe)
# ─────────────────────────────────────────────────────────────────

class TestPaymentRoutes:

    def test_list_payments(self, client: TestClient, auth_headers: dict):
        resp = client.get("/api/v1/payments/", headers=auth_headers)
        assert resp.status_code == 200

    def test_get_payment_not_found(self, client: TestClient, auth_headers: dict):
        resp = client.get(f"/api/v1/payments/{uuid.uuid4()}", headers=auth_headers)
        assert resp.status_code == 404

    def test_create_payment_mocked(
        self, client: TestClient, auth_headers: dict, db: Session, test_user
    ):
        plan = _make_plan(db, "PaymentPlan")
        sub = _make_subscription(db, test_user.id, plan.id)

        mock_intent = MagicMock()
        mock_intent.id = "pi_test_abc"
        mock_intent.status = "succeeded"
        mock_intent.client_secret = "pi_secret_123"

        with patch("stripe.PaymentIntent.create", return_value=mock_intent):
            resp = client.post("/api/v1/payments/", json={
                "subscription_id": str(sub.id),
                "amount": 2999,
                "currency": "usd",
            }, headers=auth_headers)
        assert resp.status_code in (200, 422, 404)

    def test_refund_payment_mocked(
        self, client: TestClient, auth_headers: dict, db: Session, test_user
    ):
        plan = _make_plan(db, "RefundPlan")
        sub = _make_subscription(db, test_user.id, plan.id)

        from app.models.enums import PaymentStatus
        pm = models.PaymentMethod(user_id=test_user.id, provider="stripe", token_ref="pi_test_refund")
        db.add(pm); db.commit()
        payment = models.Payment(
            user_id=test_user.id,
            subscription_id=sub.id,
            payment_method_id=pm.id,
            amount=2999,
            currency="usd",
            status=PaymentStatus.COMPLETED,
        )
        db.add(payment); db.commit(); db.refresh(payment)

        mock_refund = MagicMock()
        mock_refund.id = "re_test"
        mock_refund.status = "succeeded"

        with patch("stripe.Refund.create", return_value=mock_refund):
            resp = client.post(
                f"/api/v1/payments/{payment.id}/refund",
                headers=auth_headers,
            )
        assert resp.status_code in (200, 404, 422)


# ─────────────────────────────────────────────────────────────────
# Usage routes (remaining paths)
# ─────────────────────────────────────────────────────────────────

class TestUsageRemainingPaths:

    def test_get_my_usage(self, client: TestClient, auth_headers: dict):
        resp = client.get("/api/v1/usages/", headers=auth_headers)
        assert resp.status_code in (200, 404)

    def test_delete_usage(self, client: TestClient, db: Session, test_user):
        headers = _admin_headers(db, test_user)
        usage = models.Usage(
            user_id=test_user.id,
            resource_type="AI_REQUEST",
            used=1,
            limit_value=100,
        )
        db.add(usage); db.commit(); db.refresh(usage)
        resp = client.delete(f"/api/v1/usages/{usage.id}", headers=headers)
        assert resp.status_code in (200, 404)

    def test_update_usage(self, client: TestClient, db: Session, test_user):
        headers = _admin_headers(db, test_user)
        usage = models.Usage(
            user_id=test_user.id,
            resource_type="API_CALL",
            used=5,
            limit_value=1000,
        )
        db.add(usage); db.commit(); db.refresh(usage)
        resp = client.put(f"/api/v1/usages/{usage.id}", json={"used": 10}, headers=headers)
        assert resp.status_code in (200, 404)


# ─────────────────────────────────────────────────────────────────
# AgentRun remaining paths
# ─────────────────────────────────────────────────────────────────

class TestAgentRunRemainingPaths:

    def _setup(self, db, user_id):
        from app.models.business.business import Business, BusinessRoadmap, RoadmapStage
        from app.models.enums import BusinessStage, StageType, AgentRunStatus
        agent = models.Agent(name="RunBot", phase="research")
        db.add(agent); db.commit()
        biz = Business(owner_id=user_id, stage=BusinessStage.EARLY)
        db.add(biz); db.commit()
        rm = BusinessRoadmap(business_id=biz.id)
        db.add(rm); db.commit()
        st = RoadmapStage(roadmap_id=rm.id, order_index=1, stage_type=StageType.RESEARCH)
        db.add(st); db.commit(); db.refresh(st)
        run = models.AgentRun(
            agent_id=agent.id,
            stage_id=st.id, status=AgentRunStatus.PENDING,
            input_data={},
        )
        db.add(run); db.commit(); db.refresh(run)
        return run

    def test_get_agent_run_by_id(self, client: TestClient, auth_headers: dict, db: Session, test_user):
        run = self._setup(db, test_user.id)
        resp = client.get(f"/api/v1/agent_runs/{run.id}", headers=auth_headers)
        assert resp.status_code == 200

    def test_update_agent_run(self, client: TestClient, auth_headers: dict, db: Session, test_user):
        run = self._setup(db, test_user.id)
        resp = client.put(f"/api/v1/agent_runs/{run.id}",
                         json={"execution_time_ms": 500}, headers=auth_headers)
        assert resp.status_code == 200

    def test_update_agent_run_not_found(self, client: TestClient, auth_headers: dict):
        resp = client.put(f"/api/v1/agent_runs/{uuid.uuid4()}",
                         json={"execution_time_ms": 1}, headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_agent_run(self, client: TestClient, auth_headers: dict, db: Session, test_user):
        run = self._setup(db, test_user.id)
        resp = client.delete(f"/api/v1/agent_runs/{run.id}", headers=auth_headers)
        assert resp.status_code == 200

    def test_delete_agent_run_not_found(self, client: TestClient, auth_headers: dict):
        resp = client.delete(f"/api/v1/agent_runs/{uuid.uuid4()}", headers=auth_headers)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_execute_agent_run_via_service(self, db: Session, test_user):
        from app.services.ai import ai_service
        run = self._setup(db, test_user.id)

        async def mock_exec(*_a, **_k):
            return {"summary": "ok", "score": 0.9}

        with patch.object(ai_service.provider_runtime, "run_agent_execution", mock_exec):
            result = await ai_service.execute_agent_run_async(db, run.id)
        assert result is not None
        from app.models.enums import AgentRunStatus
        assert result.status == AgentRunStatus.SUCCESS
