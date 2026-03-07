"""
Integration tests for the auth email flow:
  - POST /auth/register  → queues a verification email
  - GET  /auth/verify-email?token= → sets is_verified=True (single-use)
  - POST /auth/forgot-password → queues a password reset email
  - Full reset flow: forgot → reset-password
"""



# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

import pytest
from uuid import UUID, uuid4
from app.core.exceptions import BadRequestError

def _register_user(client, email=None, password="securepass123"):
    email = email or f"reg_{uuid4().hex[:8]}@example.com"
    return client.post(
        "/api/v1/auth/register",
        json={"name": "New User", "email": email, "password": password},
    )



# ---------------------------------------------------------------------------
# Registration + email verification flow
# ---------------------------------------------------------------------------

class TestVerificationEmailFlow:

    def test_register_queues_verification_email(self, client, mock_dispatcher):
        """POST /register must call dispatcher.emit for user.created."""
        email = f"reg_{uuid4().hex[:8]}@example.com"
        resp = _register_user(client, email=email)
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data
        assert "verify" in data["message"].lower() or "registered" in data["message"].lower()

        # Check if the event was emitted
        from unittest.mock import ANY
        mock_dispatcher.assert_called_with("auth.user_registered", {"user_id": UUID(data["id"]), "email": email, "token": ANY})

    def test_register_duplicate_email_returns_409(self, client):
        email = f"dup_{uuid4().hex[:8]}@example.com"
        _register_user(client, email=email)
        resp = _register_user(client, email=email)
        assert resp.status_code == 409

    def test_verify_email_endpoint_sets_verified(self, client, db, monkeypatch):
        """GET /verify-email with a valid token must set is_verified=True."""
        import app.models as models
        from app.core.security import create_email_verification_token
        from config.settings import settings
        import jwt
        from datetime import datetime, timezone

        # 1. Create an unverified user directly
        from app.core.security import get_password_hash
        import uuid
        email = f"verify_{uuid.uuid4().hex[:8]}@example.com"
        user = models.User(
            email=email,
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
        token_data = jwt.decode(
            token,
            settings.jwt_verify_key,
            algorithms=[settings.jwt_algorithm],
        )
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
        import jwt
        from datetime import datetime, timezone

        import uuid
        email = f"single_{uuid.uuid4().hex[:8]}@example.com"
        user = models.User(
            email=email,
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
        token_data = jwt.decode(
            token,
            settings.jwt_verify_key,
            algorithms=[settings.jwt_algorithm],
        )
        db_token = models.EmailVerificationToken(
            user_id=user.id,
            jti=token_data["jti"],
            expires_at=datetime.fromtimestamp(token_data["exp"], tz=timezone.utc),
        )
        db.add(db_token)
        db.commit()

        first = client.get(f"/api/v1/auth/verify-email?token={token}")
        assert first.status_code == 200

        with pytest.raises(BadRequestError):
            client.get(f"/api/v1/auth/verify-email?token={token}")

    def test_verify_email_invalid_token_returns_400(self, client):
        with pytest.raises(BadRequestError):
            client.get("/api/v1/auth/verify-email?token=not-a-real-token")


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Password reset email flow
# ---------------------------------------------------------------------------

class TestPasswordResetEmailFlow:

    def test_forgot_password_queues_reset_email(self, client, test_user, mock_dispatcher):
        """POST /forgot-password must call dispatcher.emit for user.password_reset_requested."""
        resp = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": test_user.email},
        )
        assert resp.status_code == 200
        assert "sent" in resp.json()["message"].lower()

        # Check if the event was emitted
        mock_dispatcher.assert_called()
        call_args = mock_dispatcher.call_args[0]
        assert call_args[0] == "auth.password_reset_requested"
        assert call_args[1]["email"] == test_user.email
        assert "token" in call_args[1]

    def test_forgot_password_unknown_email_no_leak(self, client, mock_dispatcher):
        """POST /forgot-password for unknown email must return 200 (no user enumeration)."""
        resp = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": f"ghost_{uuid4().hex[:8]}@example.com"},
        )
        assert resp.status_code == 200
        mock_dispatcher.assert_not_called()  # no email event sent for unknown user

    def test_full_reset_flow(self, client, test_user, db, mock_dispatcher):
        """forgot-password → reset-password should work end-to-end."""
        # 1. Request reset
        resp = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": test_user.email},
        )
        assert resp.status_code == 200
        
        # 2. To simulate full reset, we need a real token. Since dispatcher is mocked,
        # we will manually mint a real token via security service just like the event handler would.
        from app.core.security import create_password_reset_token
        import jwt
        from config.settings import settings
        from datetime import datetime, timezone
        import app.models as models
        
        token = create_password_reset_token(test_user.email)
        token_data = jwt.decode(
            token,
            settings.jwt_verify_key,
            algorithms=[settings.jwt_algorithm],
        )
        db_token = models.PasswordResetToken(
            user_id=test_user.id,
            jti=token_data["jti"],
            expires_at=datetime.fromtimestamp(token_data["exp"], tz=timezone.utc),
        )
        db.add(db_token)
        db.commit()

        # 3. Use the token to reset the password
        resp2 = client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "new_password": "NewP@ssword99"},
        )
        assert resp2.status_code == 200
        assert "updated" in resp2.json()["message"].lower()

        # 4. Token must be single-use
        with pytest.raises(BadRequestError):
            client.post(
                "/api/v1/auth/reset-password",
                json={"token": token, "new_password": "AnotherPass99"},
            )
