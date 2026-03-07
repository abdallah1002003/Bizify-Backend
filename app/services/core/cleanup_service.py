"""
Cleanup service for periodic removal of stale database records.
"""
from __future__ import annotations

import logging

from typing import cast
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.base_service import BaseService
from app.repositories.auth_repository import RefreshTokenRepository, PasswordResetTokenRepository, EmailVerificationTokenRepository

logger = logging.getLogger(__name__)

class CleanupService(BaseService):
    """Service for periodic database cleanup tasks."""
    db: AsyncSession

    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.refresh_token_repo = RefreshTokenRepository(db)
        self.password_reset_token_repo = PasswordResetTokenRepository(db)
        self.email_verify_token_repo = EmailVerificationTokenRepository(db)

    async def cleanup_expired_refresh_tokens(self) -> int:
        """Remove expired refresh tokens. Returns count of deleted rows."""
        try:
            deleted = await self.refresh_token_repo.delete_expired()
            if deleted:
                logger.info("Cleaned up %d expired refresh tokens", deleted)
            return cast(int, deleted)
        except Exception:
            await self.refresh_token_repo.rollback()
            logger.exception("Failed to clean up expired refresh tokens")
            return 0

    async def cleanup_expired_password_reset_tokens(self) -> int:
        """Remove expired or used password reset tokens."""
        try:
            deleted = await self.password_reset_token_repo.delete_expired_or_used()
            if deleted:
                logger.info("Cleaned up %d expired/used password reset tokens", deleted)
            return cast(int, deleted)
        except Exception:
            await self.password_reset_token_repo.rollback()
            logger.exception("Failed to clean up expired password reset tokens")
            return 0

    async def cleanup_expired_verification_tokens(self) -> int:
        """Remove expired or used email verification tokens."""
        try:
            deleted = await self.email_verify_token_repo.delete_expired_or_used()
            if deleted:
                logger.info("Cleaned up %d expired/used email verification tokens", deleted)
            return cast(int, deleted)
        except Exception:
            await self.email_verify_token_repo.rollback()
            logger.exception("Failed to clean up expired email verification tokens")
            return 0

    async def cleanup_all(self) -> dict:
        """Run all cleanup tasks in sequence."""
        return {
            "refresh_tokens": await self.cleanup_expired_refresh_tokens(),
            "password_reset_tokens": await self.cleanup_expired_password_reset_tokens(),
            "verification_tokens": await self.cleanup_expired_verification_tokens(),
        }

async def get_cleanup_service(db: AsyncSession) -> CleanupService:
    """Dependency provider for CleanupService."""
    return CleanupService(db)
