"""
Unit tests for cleanup_service.py.

Covers all three cleanup functions and the cleanup_all aggregate.
"""

from datetime import datetime, timedelta, timezone


import app.models as models
from app.core.security import get_password_hash
from app.services.core.cleanup_service import (
    cleanup_all,
    cleanup_expired_refresh_tokens,
    cleanup_expired_password_reset_tokens,
    cleanup_expired_verification_tokens,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc_now():
    return datetime.now(timezone.utc)


def _past(minutes=30):
    return _utc_now() - timedelta(minutes=minutes)


def _future(minutes=30):
    return _utc_now() + timedelta(minutes=minutes)


def _make_user(db):
    user = models.User(
        email=f"cleanup_{_utc_now().timestamp()}@example.com",
        name="Cleanup User",
        password_hash=get_password_hash("pass"),
        role="entrepreneur",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Refresh tokens
# ---------------------------------------------------------------------------

class TestCleanupRefreshTokens:
    def test_deletes_expired_tokens(self, db):
        user = _make_user(db)
        expired = models.RefreshToken(user_id=user.id, jti="expired-jti", expires_at=_past())
        active = models.RefreshToken(user_id=user.id, jti="active-jti", expires_at=_future())
        db.add_all([expired, active])
        db.commit()

        deleted = cleanup_expired_refresh_tokens(db)
        assert deleted == 1
        assert db.query(models.RefreshToken).filter_by(jti="expired-jti").first() is None
        assert db.query(models.RefreshToken).filter_by(jti="active-jti").first() is not None

    def test_returns_zero_when_nothing_to_clean(self, db):
        assert cleanup_expired_refresh_tokens(db) == 0


# ---------------------------------------------------------------------------
# Password reset tokens
# ---------------------------------------------------------------------------

class TestCleanupPasswordResetTokens:
    def test_deletes_expired_tokens(self, db):
        user = _make_user(db)
        expired = models.PasswordResetToken(user_id=user.id, jti="pr-expired", expires_at=_past())
        fresh = models.PasswordResetToken(user_id=user.id, jti="pr-fresh", expires_at=_future())
        db.add_all([expired, fresh])
        db.commit()

        deleted = cleanup_expired_password_reset_tokens(db)
        assert deleted == 1
        assert db.query(models.PasswordResetToken).filter_by(jti="pr-expired").first() is None

    def test_deletes_used_tokens(self, db):
        user = _make_user(db)
        used = models.PasswordResetToken(user_id=user.id, jti="pr-used", expires_at=_future(), used=True)
        db.add(used)
        db.commit()

        deleted = cleanup_expired_password_reset_tokens(db)
        assert deleted == 1


# ---------------------------------------------------------------------------
# Email verification tokens
# ---------------------------------------------------------------------------

class TestCleanupVerificationTokens:
    def test_deletes_expired_tokens(self, db):
        user = _make_user(db)
        expired = models.EmailVerificationToken(user_id=user.id, jti="ev-expired", expires_at=_past())
        fresh = models.EmailVerificationToken(user_id=user.id, jti="ev-fresh", expires_at=_future())
        db.add_all([expired, fresh])
        db.commit()

        deleted = cleanup_expired_verification_tokens(db)
        assert deleted == 1
        assert db.query(models.EmailVerificationToken).filter_by(jti="ev-expired").first() is None

    def test_deletes_used_tokens(self, db):
        user = _make_user(db)
        used = models.EmailVerificationToken(user_id=user.id, jti="ev-used", expires_at=_future(), used=True)
        db.add(used)
        db.commit()

        deleted = cleanup_expired_verification_tokens(db)
        assert deleted == 1


# ---------------------------------------------------------------------------
# cleanup_all aggregate
# ---------------------------------------------------------------------------

class TestCleanupAll:
    def test_returns_summary_dict(self, db):
        result = cleanup_all(db)
        assert set(result.keys()) == {"refresh_tokens", "password_reset_tokens", "verification_tokens"}
        assert all(isinstance(v, int) for v in result.values())

    def test_cleans_all_types(self, db):
        user = _make_user(db)
        db.add_all([
            models.RefreshToken(user_id=user.id, jti="all-rt", expires_at=_past()),
            models.PasswordResetToken(user_id=user.id, jti="all-pr", expires_at=_past()),
            models.EmailVerificationToken(user_id=user.id, jti="all-ev", expires_at=_past()),
        ])
        db.commit()

        summary = cleanup_all(db)
        assert summary["refresh_tokens"] >= 1
        assert summary["password_reset_tokens"] >= 1
        assert summary["verification_tokens"] >= 1
