"""
Cleanup service for periodic removal of stale database records.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import Depends
from sqlalchemy import delete, CursorResult
from typing import cast
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users.user import RefreshToken, PasswordResetToken, EmailVerificationToken
from app.services.base_service import BaseService
from app.db.database import get_async_db

logger = logging.getLogger(__name__)

class CleanupService(BaseService):
    """Service for periodic database cleanup tasks."""
    db: AsyncSession

    async def cleanup_expired_refresh_tokens(self) -> int:
        """Remove expired refresh tokens. Returns count of deleted rows."""
        try:
            now = datetime.now(timezone.utc)
            stmt = delete(RefreshToken).where(RefreshToken.expires_at < now)
            result = await self.db.execute(stmt)
            await self.db.commit()
            deleted = cast(CursorResult, result).rowcount or 0
            if deleted:
                logger.info("Cleaned up %d expired refresh tokens", deleted)
            return cast(int, deleted)
        except Exception:
            await self.db.rollback()
            logger.exception("Failed to clean up expired refresh tokens")
            return 0

    async def cleanup_expired_password_reset_tokens(self) -> int:
        """Remove expired or used password reset tokens."""
        try:
            now = datetime.now(timezone.utc)
            stmt = delete(PasswordResetToken).where(
                (PasswordResetToken.expires_at < now) | (PasswordResetToken.used == True)  # noqa: E712
            )
            result = await self.db.execute(stmt)
            await self.db.commit()
            deleted = cast(CursorResult, result).rowcount or 0
            if deleted:
                logger.info("Cleaned up %d expired/used password reset tokens", deleted)
            return cast(int, deleted)
        except Exception:
            await self.db.rollback()
            logger.exception("Failed to clean up expired password reset tokens")
            return 0

    async def cleanup_expired_verification_tokens(self) -> int:
        """Remove expired or used email verification tokens."""
        try:
            now = datetime.now(timezone.utc)
            stmt = delete(EmailVerificationToken).where(
                (EmailVerificationToken.expires_at < now) | (EmailVerificationToken.used == True)  # noqa: E712
            )
            result = await self.db.execute(stmt)
            await self.db.commit()
            deleted = cast(CursorResult, result).rowcount or 0
            if deleted:
                logger.info("Cleaned up %d expired/used email verification tokens", deleted)
            return cast(int, deleted)
        except Exception:
            await self.db.rollback()
            logger.exception("Failed to clean up expired email verification tokens")
            return 0

    async def cleanup_all(self) -> dict:
        """Run all cleanup tasks in sequence."""
        return {
            "refresh_tokens": await self.cleanup_expired_refresh_tokens(),
            "password_reset_tokens": await self.cleanup_expired_password_reset_tokens(),
            "verification_tokens": await self.cleanup_expired_verification_tokens(),
        }

async def get_cleanup_service(db: AsyncSession = Depends(get_async_db)) -> CleanupService:
    """Dependency provider for CleanupService."""
    return CleanupService(db)

# ----------------------------
# Legacy Async Aliases
# ----------------------------

async def cleanup_expired_refresh_tokens(db: AsyncSession) -> int:
    return await CleanupService(db).cleanup_expired_refresh_tokens()

async def cleanup_expired_password_reset_tokens(db: AsyncSession) -> int:
    return await CleanupService(db).cleanup_expired_password_reset_tokens()

async def cleanup_expired_verification_tokens(db: AsyncSession) -> int:
    return await CleanupService(db).cleanup_expired_verification_tokens()

async def cleanup_all(db: AsyncSession) -> dict:
    return await CleanupService(db).cleanup_all()

# Keep legacy alias
cleanup_expired_tokens = cleanup_expired_refresh_tokens
