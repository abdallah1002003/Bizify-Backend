from datetime import datetime, timedelta, timezone
import logging
from typing import Optional, Tuple
from uuid import UUID

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import jwt

import app.models as models
from app.db.database import get_async_db
from app.core import security
from app.services.base_service import BaseService
from app.services.interfaces import IUserService
from app.services.users.user_service import UserService, get_user_service
from app.core.events import dispatcher
from config.settings import settings

logger = logging.getLogger(__name__)


class AuthService(BaseService):
    """Service for handling authentication and token management (Asynchronous)."""
    db: AsyncSession

    def __init__(self, db: AsyncSession, user_service: IUserService):
        super().__init__(db)
        self.users = user_service

    async def _persist_refresh_token(self, user_id: UUID, refresh_token: str) -> None:
        """Persists a refresh token in the database."""
        try:
            token_data = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            db_token = models.RefreshToken(
                user_id=user_id,
                jti=token_data["jti"],
                expires_at=datetime.fromtimestamp(token_data["exp"], tz=timezone.utc),
            )
            self.db.add(db_token)
            await self.db.commit()
        except jwt.PyJWTError as e:
            logger.error(f"Failed to persist refresh token: {e}")
            raise HTTPException(status_code=401, detail="Invalid refresh token")

    async def authenticate_user(self, email: str, password: str) -> Optional[models.User]:
        """Authenticates a user by email and password."""
        user = await self.users.get_user_by_email(email)
        if not user or not security.verify_password(password, user.password_hash):
            return None
        return user

    async def create_tokens(self, user_id: UUID) -> Tuple[str, str]:
        """Creates access and refresh tokens for a user and persists the refresh token."""
        access_token = security.create_access_token(
            user_id, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        refresh_token = security.create_refresh_token(user_id)
        await self._persist_refresh_token(user_id, refresh_token)
        return access_token, refresh_token

    async def refresh_access_token(self, refresh_token: str) -> Tuple[str, str]:
        """Refreshes an access token using a valid refresh token."""
        try:
            token_data = jwt.decode(
                refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            if token_data.get("type") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid token type")
            user_id_str = token_data.get("sub")
            if not user_id_str:
                raise HTTPException(status_code=401, detail="Invalid token payload")
            user_id = UUID(user_id_str)
        except (jwt.PyJWTError, ValueError):
            raise HTTPException(status_code=401, detail="Could not validate refresh token")

        user = await self.users.get_user(id=user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Inactive or non-existent user")

        jti = token_data.get("jti")
        stmt = select(models.RefreshToken).where(models.RefreshToken.jti == jti)
        result = await self.db.execute(stmt)
        stored_token = result.scalar_one_or_none()
        
        if not stored_token or stored_token.revoked:
            raise HTTPException(status_code=401, detail="Token has been revoked")

        # Invalidate old token
        stored_token.revoked = True
        self.db.add(stored_token)
        await self.db.commit()

        # Create new tokens
        return await self.create_tokens(user.id)

    async def revoke_refresh_token(self, refresh_token: str) -> None:
        """Revokes a refresh token."""
        try:
            token_data = jwt.decode(
                refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            jti = token_data.get("jti")
            stmt = select(models.RefreshToken).where(models.RefreshToken.jti == jti)
            result = await self.db.execute(stmt)
            stored = result.scalar_one_or_none()
            if stored:
                stored.revoked = True
                await self.db.commit()
        except jwt.PyJWTError:
            pass  # Silent fail for invalid tokens

    async def create_verification_token(self, user_id: UUID, email: str) -> str:
        """Creates and persists an email verification token."""
        token = security.create_email_verification_token(email)
        token_data = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        db_token = models.EmailVerificationToken(
            user_id=user_id,
            jti=token_data["jti"],
            expires_at=datetime.fromtimestamp(token_data["exp"], tz=timezone.utc),
        )
        self.db.add(db_token)
        await self.db.commit()
        
        # Emit event for email delivery or other side effects
        await dispatcher.emit("auth.user_registered", {"email": email, "token": token, "user_id": user_id})
        
        return token

    async def verify_email(self, token: str) -> models.User:
        """Verifies an email using a token."""
        token_payload = security.verify_email_verification_token(token)
        if not token_payload:
            raise HTTPException(status_code=400, detail="Invalid or expired verification token")

        email_raw = token_payload.get("sub")
        if not email_raw:
            raise HTTPException(status_code=400, detail="Invalid token payload")
        email = str(email_raw)
        jti = token_payload.get("jti")

        # JTI Blacklist check
        from app.core.token_blacklist import is_token_blacklisted, blacklist_token
        if jti and await is_token_blacklisted(jti):
            raise HTTPException(status_code=400, detail="Verification link has already been used")

        stmt = select(models.EmailVerificationToken).where(models.EmailVerificationToken.jti == jti)
        result = await self.db.execute(stmt)
        stored_token = result.scalar_one_or_none()
        
        if not stored_token or stored_token.used:
            raise HTTPException(
                status_code=400, detail="Verification link has already been used or is invalid"
            )

        user = await self.users.get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.is_verified:
            user.is_verified = True
            stored_token.used = True
            self.db.add(user)
            self.db.add(stored_token)
            await self.db.commit()

        # Blacklist the token after successful use
        exp = token_payload.get("exp")
        if jti and exp:
            remaining_ttl = int(exp - datetime.now(timezone.utc).timestamp())
            await blacklist_token(jti, remaining_ttl)

        return user

    async def request_password_reset(self, email: str) -> None:
        """Initiates a password reset request and emits an event."""
        user = await self.users.get_user_by_email(email)
        if not user:
            return

        token = security.create_password_reset_token(user.email)
        token_data = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        db_token = models.PasswordResetToken(
            user_id=user.id,
            jti=token_data["jti"],
            expires_at=datetime.fromtimestamp(token_data["exp"], tz=timezone.utc),
        )
        self.db.add(db_token)
        await self.db.commit()

        # Emit event for email delivery
        await dispatcher.emit("auth.password_reset_requested", {"email": email, "token": token, "user_id": user.id})


async def get_auth_service(
    db: AsyncSession = Depends(get_async_db),
    user_service: UserService = Depends(get_user_service)
) -> AuthService:
    """Dependency provider for AuthService."""
    return AuthService(db, user_service)
