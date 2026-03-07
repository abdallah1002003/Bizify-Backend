"""
Cleanup service for periodic removal of stale database records.
"""
from __future__ import annotations

import logging
<<<<<<< HEAD

from typing import cast
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.base_service import BaseService
from app.repositories.auth_repository import RefreshTokenRepository, PasswordResetTokenRepository, EmailVerificationTokenRepository
=======
from datetime import datetime, timezone

from fastapi import Depends
from sqlalchemy import delete, CursorResult
from typing import cast
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users.user import RefreshToken, PasswordResetToken, EmailVerificationToken
from app.services.base_service import BaseService
from app.db.database import get_async_db
>>>>>>> origin/main

logger = logging.getLogger(__name__)

class CleanupService(BaseService):
    """Service for periodic database cleanup tasks."""
    db: AsyncSession

<<<<<<< HEAD
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.refresh_token_repo = RefreshTokenRepository(db)
        self.password_reset_token_repo = PasswordResetTokenRepository(db)
        self.email_verify_token_repo = EmailVerificationTokenRepository(db)

    async def cleanup_expired_refresh_tokens(self) -> int:
        """Remove expired refresh tokens. Returns count of deleted rows."""
        try:
            deleted = await self.refresh_token_repo.delete_expired()
=======
    async def cleanup_expired_refresh_tokens(self) -> int:
        """Remove expired refresh tokens. Returns count of deleted rows."""
        try:
            now = datetime.now(timezone.utc)
            stmt = delete(RefreshToken).where(RefreshToken.expires_at < now)
            result = await self.db.execute(stmt)
            await self.db.commit()
            deleted = cast(CursorResult, result).rowcount or 0
>>>>>>> origin/main
            if deleted:
                logger.info("Cleaned up %d expired refresh tokens", deleted)
            return cast(int, deleted)
        except Exception:
<<<<<<< HEAD
            await self.refresh_token_repo.rollback()
=======
            await self.db.rollback()
>>>>>>> origin/main
            logger.exception("Failed to clean up expired refresh tokens")
            return 0

    async def cleanup_expired_password_reset_tokens(self) -> int:
        """Remove expired or used password reset tokens."""
        try:
<<<<<<< HEAD
            deleted = await self.password_reset_token_repo.delete_expired_or_used()
=======
            now = datetime.now(timezone.utc)
            stmt = delete(PasswordResetToken).where(
                (PasswordResetToken.expires_at < now) | (PasswordResetToken.used == True)  # noqa: E712
            )
            result = await self.db.execute(stmt)
            await self.db.commit()
            deleted = cast(CursorResult, result).rowcount or 0
>>>>>>> origin/main
            if deleted:
                logger.info("Cleaned up %d expired/used password reset tokens", deleted)
            return cast(int, deleted)
        except Exception:
<<<<<<< HEAD
            await self.password_reset_token_repo.rollback()
=======
            await self.db.rollback()
>>>>>>> origin/main
            logger.exception("Failed to clean up expired password reset tokens")
            return 0

    async def cleanup_expired_verification_tokens(self) -> int:
        """Remove expired or used email verification tokens."""
        try:
<<<<<<< HEAD
            deleted = await self.email_verify_token_repo.delete_expired_or_used()
=======
            now = datetime.now(timezone.utc)
            stmt = delete(EmailVerificationToken).where(
                (EmailVerificationToken.expires_at < now) | (EmailVerificationToken.used == True)  # noqa: E712
            )
            result = await self.db.execute(stmt)
            await self.db.commit()
            deleted = cast(CursorResult, result).rowcount or 0
>>>>>>> origin/main
            if deleted:
                logger.info("Cleaned up %d expired/used email verification tokens", deleted)
            return cast(int, deleted)
        except Exception:
<<<<<<< HEAD
            await self.email_verify_token_repo.rollback()
=======
            await self.db.rollback()
>>>>>>> origin/main
            logger.exception("Failed to clean up expired email verification tokens")
            return 0

    async def cleanup_all(self) -> dict:
        """Run all cleanup tasks in sequence."""
        return {
            "refresh_tokens": await self.cleanup_expired_refresh_tokens(),
            "password_reset_tokens": await self.cleanup_expired_password_reset_tokens(),
            "verification_tokens": await self.cleanup_expired_verification_tokens(),
        }

<<<<<<< HEAD
async def get_cleanup_service(db: AsyncSession) -> CleanupService:
    """Dependency provider for CleanupService."""
    return CleanupService(db)
=======
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
>>>>>>> origin/main
