import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import select

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


async def _make_user(db):
    user = models.User(
        email=f"cleanup_{_utc_now().timestamp()}@example.com",
        name="Cleanup User",
        password_hash=get_password_hash("pass"),
        role="entrepreneur",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Refresh tokens
# ---------------------------------------------------------------------------

class TestCleanupRefreshTokens:
    @pytest.mark.asyncio
    async def test_deletes_expired_tokens(self, async_db):
        user = await _make_user(async_db)
        expired = models.RefreshToken(user_id=user.id, jti="expired-jti", expires_at=_past())
        active = models.RefreshToken(user_id=user.id, jti="active-jti", expires_at=_future())
        async_db.add_all([expired, active])
        await async_db.commit()

        deleted = await cleanup_expired_refresh_tokens(async_db)
        assert deleted == 1
        
        stmt_expired = select(models.RefreshToken).filter_by(jti="expired-jti")
        result_expired = await async_db.execute(stmt_expired)
        assert result_expired.scalar_one_or_none() is None
        
        stmt_active = select(models.RefreshToken).filter_by(jti="active-jti")
        result_active = await async_db.execute(stmt_active)
        assert result_active.scalar_one_or_none() is not None

    @pytest.mark.asyncio
    async def test_returns_zero_when_nothing_to_clean(self, async_db):
        assert await cleanup_expired_refresh_tokens(async_db) == 0


# ---------------------------------------------------------------------------
# Password reset tokens
# ---------------------------------------------------------------------------

class TestCleanupPasswordResetTokens:
    @pytest.mark.asyncio
    async def test_deletes_expired_tokens(self, async_db):
        user = await _make_user(async_db)
        expired = models.PasswordResetToken(user_id=user.id, jti="pr-expired", expires_at=_past())
        fresh = models.PasswordResetToken(user_id=user.id, jti="pr-fresh", expires_at=_future())
        async_db.add_all([expired, fresh])
        await async_db.commit()

        deleted = await cleanup_expired_password_reset_tokens(async_db)
        assert deleted == 1
        
        stmt = select(models.PasswordResetToken).filter_by(jti="pr-expired")
        result = await async_db.execute(stmt)
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_deletes_used_tokens(self, async_db):
        user = await _make_user(async_db)
        used = models.PasswordResetToken(user_id=user.id, jti="pr-used", expires_at=_future(), used=True)
        async_db.add(used)
        await async_db.commit()

        deleted = await cleanup_expired_password_reset_tokens(async_db)
        assert deleted == 1


# ---------------------------------------------------------------------------
# Email verification tokens
# ---------------------------------------------------------------------------

class TestCleanupVerificationTokens:
    @pytest.mark.asyncio
    async def test_deletes_expired_tokens(self, async_db):
        user = await _make_user(async_db)
        expired = models.EmailVerificationToken(user_id=user.id, jti="ev-expired", expires_at=_past())
        fresh = models.EmailVerificationToken(user_id=user.id, jti="ev-fresh", expires_at=_future())
        async_db.add_all([expired, fresh])
        await async_db.commit()

        deleted = await cleanup_expired_verification_tokens(async_db)
        assert deleted == 1
        
        stmt = select(models.EmailVerificationToken).filter_by(jti="ev-expired")
        result = await async_db.execute(stmt)
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_deletes_used_tokens(self, async_db):
        user = await _make_user(async_db)
        used = models.EmailVerificationToken(user_id=user.id, jti="ev-used", expires_at=_future(), used=True)
        async_db.add(used)
        await async_db.commit()

        deleted = await cleanup_expired_verification_tokens(async_db)
        assert deleted == 1


# ---------------------------------------------------------------------------
# cleanup_all aggregate
# ---------------------------------------------------------------------------

class TestCleanupAll:
    @pytest.mark.asyncio
    async def test_returns_summary_dict(self, async_db):
        result = await cleanup_all(async_db)
        assert set(result.keys()) == {"refresh_tokens", "password_reset_tokens", "verification_tokens"}
        assert all(isinstance(v, int) for v in result.values())

    @pytest.mark.asyncio
    async def test_cleans_all_types(self, async_db):
        user = await _make_user(async_db)
        async_db.add_all([
            models.RefreshToken(user_id=user.id, jti="all-rt", expires_at=_past()),
            models.PasswordResetToken(user_id=user.id, jti="all-pr", expires_at=_past()),
            models.EmailVerificationToken(user_id=user.id, jti="all-ev", expires_at=_past()),
        ])
        await async_db.commit()

        summary = await cleanup_all(async_db)
        assert summary["refresh_tokens"] >= 1
        assert summary["password_reset_tokens"] >= 1
        assert summary["verification_tokens"] >= 1
