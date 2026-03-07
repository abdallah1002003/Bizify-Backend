"""
Repository for auth-related database models:
  - RefreshToken
  - EmailVerificationToken
  - PasswordResetToken

# NOTE (Architecture - Afnan):
# Service → Repository → Database
# AuthService should delegate all token persistence to this repository.
"""
from typing import Optional

from sqlalchemy import select, delete, CursorResult
from sqlalchemy.ext.asyncio import AsyncSession
from typing import cast
from datetime import datetime, timezone

from app.models.users.user import RefreshToken, EmailVerificationToken, PasswordResetToken
from app.repositories.base_repository import GenericRepository


class RefreshTokenRepository(GenericRepository[RefreshToken]):
    """Repository for RefreshToken model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, RefreshToken)

    async def get_by_jti(self, jti: str) -> Optional[RefreshToken]:
        """Retrieve a refresh token by its JWT ID."""
        stmt = select(RefreshToken).where(RefreshToken.jti == jti)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_safe(self, obj_in: dict, auto_commit: bool = True) -> Optional[RefreshToken]:
        """Create a refresh token safely, returning None on IntegrityError (duplicate jti)."""
        from sqlalchemy.exc import IntegrityError
        try:
            return await self.create(obj_in, auto_commit=auto_commit)
        except IntegrityError:
            await self.db.rollback()
            return None

    async def revoke(self, jti: str) -> Optional[RefreshToken]:
        """Mark a refresh token as revoked. Returns the token if found."""
        token = await self.get_by_jti(jti)
        if token:
            await self.update(token, {"revoked": True})
        return token

    async def delete_expired(self) -> int:
        """Remove expired refresh tokens. Returns count of deleted rows."""
        now = datetime.now(timezone.utc)
        stmt = delete(self.model).where(self.model.expires_at < now)
        result = await self.db.execute(stmt)
        await self.db.commit()
        return cast(int, cast(CursorResult, result).rowcount or 0)


class EmailVerificationTokenRepository(GenericRepository[EmailVerificationToken]):
    """Repository for EmailVerificationToken model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, EmailVerificationToken)

    async def get_by_jti(self, jti: str) -> Optional[EmailVerificationToken]:
        """Retrieve an email verification token by its JWT ID."""
        stmt = select(EmailVerificationToken).where(EmailVerificationToken.jti == jti)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_safe(self, obj_in: dict, auto_commit: bool = True) -> Optional[EmailVerificationToken]:
        """Create a verification token safely, returning None on IntegrityError (duplicate jti)."""
        from sqlalchemy.exc import IntegrityError
        try:
            return await self.create(obj_in, auto_commit=auto_commit)
        except IntegrityError:
            await self.db.rollback()
            return None

    async def mark_used(
        self,
        token: EmailVerificationToken,
        auto_commit: bool = True,
    ) -> EmailVerificationToken:
        """Mark a verification token as used."""
        token.used = True
        self.db.add(token)
        if auto_commit:
            await self.db.commit()
        else:
            await self.db.flush()
        return token

    async def delete_expired_or_used(self) -> int:
        """Delete tokens that are expired or already used."""
        now = datetime.now(timezone.utc)
        stmt = delete(self.model).where(
            (self.model.expires_at < now) | (self.model.used.is_(True))
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return cast(int, cast(CursorResult, result).rowcount or 0)


class PasswordResetTokenRepository(GenericRepository[PasswordResetToken]):
    """Repository for PasswordResetToken model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, PasswordResetToken)

    async def get_by_jti(self, jti: str) -> Optional[PasswordResetToken]:
        """Retrieve a password reset token by its JWT ID."""
        stmt = select(PasswordResetToken).where(PasswordResetToken.jti == jti)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_safe(self, obj_in: dict, auto_commit: bool = True) -> Optional[PasswordResetToken]:
        """Create a reset token safely, returning None on IntegrityError (duplicate jti)."""
        from sqlalchemy.exc import IntegrityError
        try:
            return await self.create(obj_in, auto_commit=auto_commit)
        except IntegrityError:
            await self.db.rollback()
            return None

    async def mark_used(
        self,
        token: PasswordResetToken,
        auto_commit: bool = True,
    ) -> PasswordResetToken:
        """Mark a password reset token as used."""
        token.used = True
        self.db.add(token)
        if auto_commit:
            await self.db.commit()
        else:
            await self.db.flush()
        return token

    async def delete_expired_or_used(self) -> int:
        """Delete tokens that are expired or already used."""
        now = datetime.now(timezone.utc)
        stmt = delete(self.model).where(
            (self.model.expires_at < now) | (self.model.used.is_(True))
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return cast(int, cast(CursorResult, result).rowcount or 0)
