# ruff: noqa
"""
Coverage boost: AI API routes, billing API routes, RateLimiter middleware,
encryption, and AgentService CRUD.

All HTTP-level tests use the shared conftest fixtures (client, auth_headers, test_user).
Unit-level tests directly exercise the service/utility classes.
"""
from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.models as models


# ─────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────

def _make_agent(db: Session, name: str = "TestBot", phase: str = "research") -> models.Agent:
    agent = models.Agent(name=name, phase=phase)
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


def _make_roadmap_stage(db: Session, owner_id) -> tuple:
    from app.models.business.business import Business, BusinessRoadmap, RoadmapStage
    from app.models.enums import BusinessStage, StageType

    biz = Business(owner_id=owner_id, stage=BusinessStage.EARLY)
    db.add(biz)
    db.commit()

    roadmap = BusinessRoadmap(business_id=biz.id)
    db.add(roadmap)
    db.commit()

    stage = RoadmapStage(roadmap_id=roadmap.id, order_index=1, stage_type=StageType.RESEARCH)
    db.add(stage)
    db.commit()
    db.refresh(stage)
    return biz, roadmap, stage


# ─────────────────────────────────────────────────────────────────
# 1. AI Agent API routes
# ─────────────────────────────────────────────────────────────────

class TestAgentAPIRoutes:
    """Exercise /api/v1/agents CRUD endpoints."""

    def test_list_agents(self, client: TestClient, auth_headers: dict):
        resp = client.get("/api/v1/agents/", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_create_agent(self, client: TestClient, auth_headers: dict):
        resp = client.post(
            "/api/v1/agents/",
            json={"name": "Planner", "phase": "discovery"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Planner"
        assert data["phase"] == "discovery"

    def test_get_agent_by_id(self, client: TestClient, auth_headers: dict, db: Session):
        agent = _make_agent(db, "GetMe", "validation")
        resp = client.get(f"/api/v1/agents/{agent.id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == str(agent.id)

    def test_get_agent_not_found(self, client: TestClient, auth_headers: dict):
        resp = client.get(f"/api/v1/agents/{uuid.uuid4()}", headers=auth_headers)
        assert resp.status_code == 404

    def test_update_agent(self, client: TestClient, auth_headers: dict, db: Session):
        agent = _make_agent(db, "OldName", "research")
        resp = client.put(
            f"/api/v1/agents/{agent.id}",
            json={"name": "NewName"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "NewName"

    def test_update_agent_not_found(self, client: TestClient, auth_headers: dict):
        resp = client.put(
            f"/api/v1/agents/{uuid.uuid4()}",
            json={"name": "Ghost"},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_delete_agent(self, client: TestClient, auth_headers: dict, db: Session):
        agent = _make_agent(db, "DeleteMe", "analysis")
        resp = client.delete(f"/api/v1/agents/{agent.id}", headers=auth_headers)
        assert resp.status_code == 200

    def test_delete_agent_not_found(self, client: TestClient, auth_headers: dict):
        resp = client.delete(f"/api/v1/agents/{uuid.uuid4()}", headers=auth_headers)
        assert resp.status_code == 404

    def test_requires_auth(self, client: TestClient):
        resp = client.get("/api/v1/agents/")
        assert resp.status_code == 401


# ─────────────────────────────────────────────────────────────────
# 2. AI AgentRun API routes
# ─────────────────────────────────────────────────────────────────

class TestAgentRunAPIRoutes:
    """Exercise /api/v1/agent_runs endpoints."""

    def test_list_agent_runs(self, client: TestClient, auth_headers: dict):
        resp = client.get("/api/v1/agent_runs/", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_create_agent_run(
        self, client: TestClient, auth_headers: dict, db: Session, test_user
    ):
        agent = _make_agent(db, "RunnerBot", "research")
        _, _, stage = _make_roadmap_stage(db, test_user.id)
        resp = client.post(
            "/api/v1/agent_runs/",
            json={
                "agent_id": str(agent.id),
                "stage_id": str(stage.id),
                "input_data": {"x": 1},
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["agent_id"] == str(agent.id)

    def test_get_agent_run_not_found(self, client: TestClient, auth_headers: dict):
        resp = client.get(f"/api/v1/agent_runs/{uuid.uuid4()}", headers=auth_headers)
        assert resp.status_code == 404

    def test_list_agent_runs_filtered_by_user(
        self, client: TestClient, auth_headers: dict, db: Session, test_user
    ):
        resp = client.get(
            "/api/v1/agent_runs/",
            params={"user_id": str(test_user.id)},
            headers=auth_headers,
        )
        assert resp.status_code == 200


# ─────────────────────────────────────────────────────────────────
# 3. Billing Usage API routes
# ─────────────────────────────────────────────────────────────────

class TestUsageAPIRoutes:
    """Exercise /api/v1/usages CRUD endpoints."""

    def _make_admin(self, db: Session, user: models.User) -> dict:
        from app.models.enums import UserRole
        from app.core.security import create_access_token
        user.role = UserRole.ADMIN
        db.add(user)
        db.commit()
        return {"Authorization": f"Bearer {create_access_token(subject=str(user.id))}"}

    def test_list_usages(self, client: TestClient, auth_headers: dict):
        resp = client.get("/api/v1/usages/", headers=auth_headers)
        assert resp.status_code == 200

    def test_create_usage(
        self, client: TestClient, db: Session, test_user: models.User
    ):
        headers = self._make_admin(db, test_user)
        resp = client.post(
            "/api/v1/usages/",
            json={
                "user_id": str(test_user.id),
                "resource_type": "AI_REQUEST",
                "used": 5,
                "limit_value": 100,
            },
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["resource_type"] == "AI_REQUEST"

    def test_get_usage_not_found(self, client: TestClient, auth_headers: dict):
        resp = client.get(f"/api/v1/usages/{uuid.uuid4()}", headers=auth_headers)
        assert resp.status_code == 404


# ─────────────────────────────────────────────────────────────────
# 4. Billing Payment Method API routes
# ─────────────────────────────────────────────────────────────────

class TestPaymentMethodAPIRoutes:
    """Exercise /api/v1/payment_methods endpoints."""

    def test_list_payment_methods(self, client: TestClient, auth_headers: dict):
        resp = client.get("/api/v1/payment_methods/", headers=auth_headers)
        assert resp.status_code == 200

    def test_create_payment_method(
        self, client: TestClient, auth_headers: dict, test_user
    ):
        resp = client.post(
            "/api/v1/payment_methods/",
            json={
                "user_id": str(test_user.id),
                "provider": "stripe",
                "token_ref": "tok_test_visa",
                "last4": "4242",
                "is_default": True,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["provider"] == "stripe"

    def test_get_payment_method_not_found(self, client: TestClient, auth_headers: dict):
        resp = client.get(f"/api/v1/payment_methods/{uuid.uuid4()}", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_payment_method(
        self, client: TestClient, auth_headers: dict, test_user
    ):
        resp = client.post(
            "/api/v1/payment_methods/",
            json={
                "user_id": str(test_user.id),
                "provider": "stripe",
                "token_ref": "tok_delete_me",
                "last4": "9999",
                "is_default": False,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        mid = resp.json()["id"]
        resp = client.delete(f"/api/v1/payment_methods/{mid}", headers=auth_headers)
        assert resp.status_code == 200


# ─────────────────────────────────────────────────────────────────
# 5. RateLimiterMiddleware unit tests (bypass APP_ENV=test guard via mock)
# ─────────────────────────────────────────────────────────────────

class TestRateLimiterMiddleware:
    """Unit tests for the in-memory RateLimiterMiddleware."""

    def test_allows_requests_under_limit(self):
        from app.middleware.rate_limiter import RateLimiterMiddleware
        mw = RateLimiterMiddleware(app=None, requests_per_minute=60)
        assert mw.requests_per_minute == 60
        assert mw.window_size == 60

    def test_get_client_ip_with_client(self):
        from app.middleware.rate_limiter import RateLimiterMiddleware
        from unittest.mock import MagicMock
        mw = RateLimiterMiddleware(app=None, requests_per_minute=60)

        request = MagicMock()
        request.client.host = "192.168.1.100"
        ip = mw._get_client_ip(request)
        assert ip == "192.168.1.100"

    def test_get_client_ip_without_client(self):
        from app.middleware.rate_limiter import RateLimiterMiddleware
        from unittest.mock import MagicMock
        mw = RateLimiterMiddleware(app=None, requests_per_minute=60)

        request = MagicMock()
        request.client = None
        ip = mw._get_client_ip(request)
        assert ip == "127.0.0.1"

    def test_strict_rate_limit_paths(self):
        from app.middleware.rate_limiter import STRICT_RATE_LIMIT_PATHS
        assert "/api/v1/auth/login" in STRICT_RATE_LIMIT_PATHS
        assert STRICT_RATE_LIMIT_PATHS["/api/v1/auth/login"] <= 10

    @pytest.mark.asyncio
    async def test_rate_limit_blocking(self):
        """Middleware blocks when window is full — bypasses APP_ENV guard."""
        from app.middleware.rate_limiter import RateLimiterMiddleware
        from unittest.mock import AsyncMock, MagicMock

        mw = RateLimiterMiddleware(app=None, requests_per_minute=2)

        # Patch APP_ENV so guard doesn't skip rate limiting
        with patch("app.middleware.rate_limiter.settings") as mock_settings:
            mock_settings.APP_ENV = "production"
            mock_settings.RATE_LIMIT_PER_MINUTE = 2
            mock_settings.jwt_verify_key = "secret"
            mock_settings.jwt_algorithm = "HS256"

            call_next = AsyncMock()
            call_next.return_value = MagicMock(headers={})

            def make_request(path="/api/v1/test"):
                request = MagicMock()
                request.client.host = "10.0.0.1"
                request.headers.get.return_value = None
                request.url.path = path
                return request

            # Two allowed
            r1 = await mw.dispatch(make_request(), call_next)
            r2 = await mw.dispatch(make_request(), call_next)
            # Third should be blocked
            r3 = await mw.dispatch(make_request(), call_next)
            assert r3.status_code == 429


# ─────────────────────────────────────────────────────────────────
# 6. Encryption unit tests
# ─────────────────────────────────────────────────────────────────

class TestEncryption:
    """Tests for AES-256-GCM encrypt/decrypt and EncryptedString TypeDecorator."""

    def test_encrypt_decrypt_roundtrip(self):
        from app.core.encryption import encrypt, decrypt
        plaintext = "super_secret_value_123"
        ciphertext = encrypt(plaintext)
        assert ciphertext != plaintext
        assert decrypt(ciphertext) == plaintext

    def test_encrypt_produces_different_values(self):
        """Each encryption uses a random IV, so same input → different output."""
        from app.core.encryption import encrypt
        c1 = encrypt("hello")
        c2 = encrypt("hello")
        assert c1 != c2

    def test_encrypted_string_bind_param(self):
        from app.core.encryption import EncryptedString, decrypt
        col = EncryptedString()
        result = col.process_bind_param("my_secret", dialect=None)
        assert result is not None
        assert decrypt(result) == "my_secret"

    def test_encrypted_string_none_passthrough(self):
        from app.core.encryption import EncryptedString
        col = EncryptedString()
        assert col.process_bind_param(None, dialect=None) is None
        assert col.process_result_value(None, dialect=None) is None

    def test_encrypted_string_result_value(self):
        from app.core.encryption import EncryptedString, encrypt
        col = EncryptedString()
        blob = encrypt("stored_value")
        assert col.process_result_value(blob, dialect=None) == "stored_value"

    def test_encrypted_string_corrupt_data_passthrough(self):
        """Corrupted blob returns the raw value gracefully (migration safety)."""
        from app.core.encryption import EncryptedString
        col = EncryptedString()
        result = col.process_result_value("not_valid_encrypted_data", dialect=None)
        assert result == "not_valid_encrypted_data"


# ─────────────────────────────────────────────────────────────────
# 7. AgentService (service-level CRUD, directly)
# ─────────────────────────────────────────────────────────────────

class TestAgentServiceDirect:
    """Direct service-layer tests for AgentService (not via HTTP)."""

    @pytest.mark.asyncio
    async def test_create_get_update_delete(self, async_db):
        from app.services.ai.agent_service import AgentService
        svc = AgentService(async_db)

        # Create
        agent = await svc.create_agent(name="DirectBot", phase="analysis")
        assert agent.id is not None
        assert agent.name == "DirectBot"

        # Get
        fetched = await svc.get_agent(agent.id)
        assert fetched is not None
        assert fetched.phase == "analysis"

        # Get all
        all_agents = await svc.get_agents(skip=0, limit=10)
        assert any(a.id == agent.id for a in all_agents)

        # Update
        updated = await svc.update_agent(agent, {"name": "UpdatedBot"})
        assert updated.name == "UpdatedBot"

        # Delete
        deleted = await svc.delete_agent(agent.id)
        assert deleted is not None
        assert await svc.get_agent(agent.id) is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, async_db):
        from app.services.ai.agent_service import AgentService
        result = await AgentService(async_db).delete_agent(uuid.uuid4())
        assert result is None


# ─────────────────────────────────────────────────────────────────
# 8. Auth service - uncovered paths
# ─────────────────────────────────────────────────────────────────

class TestAuthServicePaths:
    """Tests for auth_service paths not covered by API tests."""

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, async_db, test_user):
        from app.services.auth.auth_service import AuthService
        from app.services.users.user_service import UserService
        svc = AuthService(async_db, UserService(async_db))
        result = await svc.authenticate_user(test_user.email, "wrong_password")
        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_nonexistent_email(self, async_db):
        from app.services.auth.auth_service import AuthService
        from app.services.users.user_service import UserService
        svc = AuthService(async_db, UserService(async_db))
        result = await svc.authenticate_user("nobody@example.com", "pass")
        assert result is None

    @pytest.mark.asyncio
    async def test_revoke_invalid_refresh_token_silent_fail(self, db: Session, test_user):
        from app.services.auth.auth_service import AuthService
        from app.services.users.user_service import UserService
        svc = AuthService(db, UserService(db))
        # Should not raise even with a garbage token
        await svc.revoke_refresh_token("not.a.valid.token")

    @pytest.mark.asyncio
    async def test_verify_email_invalid_token(self, db: Session, test_user):
        from fastapi import HTTPException
        from app.services.auth.auth_service import AuthService
        from app.services.users.user_service import UserService
        svc = AuthService(db, UserService(db))
        with pytest.raises(HTTPException) as exc_info:
            await svc.verify_email("garbage_token")
        assert exc_info.value.status_code == 400
