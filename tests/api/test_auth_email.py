"""
Integration tests for the auth email flow:
  - POST /auth/register  → queues a verification email
  - GET  /auth/verify-email?token= → sets is_verified=True (single-use)
  - POST /auth/forgot-password → queues a password reset email
  - Full reset flow: forgot → reset-password
"""

import pytest
from unittest.mock import AsyncMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _register_user(client, email="newuser@example.com", password="securepass123"):
    return client.post(
        "/api/v1/auth/register",
        json={"name": "New User", "email": email, "password": password},
    )


# ---------------------------------------------------------------------------
# Registration + email verification flow
# ---------------------------------------------------------------------------

class TestVerificationEmailFlow:

    def test_register_queues_verification_email(self, client, monkeypatch):
        """POST /register must call send_verification_email with the user's email."""
        sent = []

        async def fake_send(email, token):
            sent.append({"email": email, "token": token})

        monkeypatch.setattr(
            "app.api.routes.auth.send_verification_email", fake_send
        )

        resp = _register_user(client)
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data
        assert "verify" in data["message"].lower() or "registered" in data["message"].lower()

        # BackgroundTasks in TestClient are executed synchronously
        assert len(sent) == 1
        assert sent[0]["email"] == "newuser@example.com"
        assert len(sent[0]["token"]) > 10  # JWT is non-trivial

    def test_register_duplicate_email_returns_409(self, client):
        _register_user(client)
        resp = _register_user(client)
        assert resp.status_code == 409

    def test_verify_email_endpoint_sets_verified(self, client, db, monkeypatch):
        """GET /verify-email with a valid token must set is_verified=True."""
        import app.models as models
        from app.core.security import create_email_verification_token
        from config.settings import settings
        from jose import jwt
        from datetime import datetime, timezone

        # 1. Create an unverified user directly
        from app.core.security import get_password_hash
        user = models.User(
            email="toverify@example.com",
            name="Verify Me",
            password_hash=get_password_hash("pass1234"),
            role="entrepreneur",
            is_active=True,
            is_verified=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # 2. Mint and persist the verification token
        token = create_email_verification_token(user.email)
        token_data = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        db_token = models.EmailVerificationToken(
            user_id=user.id,
            jti=token_data["jti"],
            expires_at=datetime.fromtimestamp(token_data["exp"], tz=timezone.utc),
        )
        db.add(db_token)
        db.commit()

        # 3. Call the endpoint
        resp = client.get(f"/api/v1/auth/verify-email?token={token}")
        assert resp.status_code == 200
        assert "verified" in resp.json()["message"].lower()

        # 4. User must now be verified
        db.refresh(user)
        assert user.is_verified is True

        # 5. Token must be marked as used
        db.refresh(db_token)
        assert db_token.used is True

    def test_verify_email_single_use(self, client, db):
        """Using the same verification token twice must return 400 on the second call."""
        import app.models as models
        from app.core.security import create_email_verification_token, get_password_hash
        from config.settings import settings
        from jose import jwt
        from datetime import datetime, timezone

        user = models.User(
            email="singleuse@example.com",
            name="Single Use",
            password_hash=get_password_hash("pass1234"),
            role="entrepreneur",
            is_active=True,
            is_verified=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_email_verification_token(user.email)
        token_data = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        db_token = models.EmailVerificationToken(
            user_id=user.id,
            jti=token_data["jti"],
            expires_at=datetime.fromtimestamp(token_data["exp"], tz=timezone.utc),
        )
        db.add(db_token)
        db.commit()

        first = client.get(f"/api/v1/auth/verify-email?token={token}")
        assert first.status_code == 200

        second = client.get(f"/api/v1/auth/verify-email?token={token}")
        assert second.status_code == 400

    def test_verify_email_invalid_token_returns_400(self, client):
        resp = client.get("/api/v1/auth/verify-email?token=not-a-real-token")
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Password reset email flow
# ---------------------------------------------------------------------------

class TestPasswordResetEmailFlow:

    def test_forgot_password_queues_reset_email(self, client, test_user, monkeypatch):
        """POST /forgot-password must call send_password_reset_email."""
        sent = []

        async def fake_send(email, token):
            sent.append({"email": email, "token": token})

        monkeypatch.setattr(
            "app.api.routes.auth.send_password_reset_email", fake_send
        )

        resp = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": test_user.email},
        )
        assert resp.status_code == 200
        assert "sent" in resp.json()["message"].lower()

        assert len(sent) == 1
        assert sent[0]["email"] == test_user.email

    def test_forgot_password_unknown_email_no_leak(self, client, monkeypatch):
        """POST /forgot-password for unknown email must return 200 (no user enumeration)."""
        sent = []

        async def fake_send(email, token):
            sent.append(email)

        monkeypatch.setattr(
            "app.api.routes.auth.send_password_reset_email", fake_send
        )

        resp = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "ghost@example.com"},
        )
        assert resp.status_code == 200
        assert len(sent) == 0  # no email sent for unknown user

    def test_full_reset_flow(self, client, test_user, db, monkeypatch):
        """forgot-password → reset-password should work end-to-end."""
        captured_token = []

        async def fake_send(email, token):
            captured_token.append(token)

        monkeypatch.setattr(
            "app.api.routes.auth.send_password_reset_email", fake_send
        )

        # 1. Request reset
        resp = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": test_user.email},
        )
        assert resp.status_code == 200
        assert len(captured_token) == 1

        # 2. Use the token to reset the password
        resp2 = client.post(
            "/api/v1/auth/reset-password",
            json={"token": captured_token[0], "new_password": "NewP@ssword99"},
        )
        assert resp2.status_code == 200
        assert "updated" in resp2.json()["message"].lower()

        # 3. Token must be single-use
        resp3 = client.post(
            "/api/v1/auth/reset-password",
            json={"token": captured_token[0], "new_password": "AnotherPass99"},
        )
        assert resp3.status_code == 400
