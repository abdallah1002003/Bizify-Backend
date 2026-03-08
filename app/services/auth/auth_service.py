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
from app.core.metrics import active_sessions
from config.settings import settings

from app.repositories.auth_repository import RefreshTokenRepository, EmailVerificationTokenRepository, PasswordResetTokenRepository
from app.repositories.user_repository import UserRepository
from app.core.exceptions import AuthenticationError, BadRequestError, ResourceNotFoundError
from app.core.token_blacklist import is_token_blacklisted, blacklist_token

logger = logging.getLogger(__name__)


class AuthService(BaseService):
    """Service for handling authentication and token management (Asynchronous)."""
    db: AsyncSession

    def __init__(self, db: AsyncSession, user_service: IUserService):
        super().__init__(db)
        self.users = user_service
        self.refresh_token_repo = RefreshTokenRepository(db)
        self.email_verification_repo = EmailVerificationTokenRepository(db)
        self.password_reset_repo = PasswordResetTokenRepository(db)

    async def _persist_refresh_token(self, user_id: UUID, refresh_token: str) -> None:
        """Persists a refresh token in the database."""
        try:
            token_data = jwt.decode(
                refresh_token,
                settings.jwt_verify_key,
                algorithms=[settings.jwt_algorithm],
            )
            await self.refresh_token_repo.create({
                "user_id": user_id,
                "jti": token_data["jti"],
                "expires_at": datetime.fromtimestamp(token_data["exp"], tz=timezone.utc),
            })
        except jwt.PyJWTError as e:
            logger.error(f"Failed to decode refresh token: {e}")
            raise AuthenticationError("Invalid refresh token") from e

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
        active_sessions.inc() # Metrics: Track active session
        return access_token, refresh_token

    async def refresh_access_token(self, refresh_token: str) -> Tuple[str, str]:
        """Refreshes an access token using a valid refresh token."""
        try:
            token_data = jwt.decode(
                refresh_token,
                settings.jwt_verify_key,
                algorithms=[settings.jwt_algorithm],
            )
            if token_data.get("type") != "refresh":
                raise AuthenticationError("Invalid token type")
            user_id_str = token_data.get("sub")
            if not user_id_str:
                raise AuthenticationError("Invalid token payload")
            user_id = UUID(user_id_str)
        except (jwt.PyJWTError, ValueError) as e:
            raise AuthenticationError("Could not validate refresh token") from e

        user = await self.users.get_user(id=user_id)
        if not user or not user.is_active:
            raise AuthenticationError("Inactive or non-existent user")

        jti = token_data.get("jti")
        if not jti:
            raise AuthenticationError("Invalid token payload")
            
        stored_token = await self.refresh_token_repo.get_by_jti(jti)
        
        if not stored_token or stored_token.revoked:
            raise AuthenticationError("Token has been revoked")

        # Invalidate old token
        await self.refresh_token_repo.update(stored_token, {"revoked": True})

        # Create new tokens
        return await self.create_tokens(user.id)

    async def revoke_refresh_token(self, refresh_token: str) -> None:
        """Revokes a refresh token."""
        try:
            token_data = jwt.decode(
                refresh_token,
                settings.jwt_verify_key,
                algorithms=[settings.jwt_algorithm],
            )
            jti = token_data.get("jti")
            stored = await self.refresh_token_repo.get_by_jti(jti)
            if stored:
                await self.refresh_token_repo.update(stored, {"revoked": True})
                active_sessions.dec() # Metrics: Decrease active session count
        except jwt.PyJWTError:
            pass  # Silent fail for invalid tokens

    async def create_verification_token(self, user_id: UUID, email: str) -> str:
        """Creates and persists an email verification token."""
        token = security.create_email_verification_token(email)
        token_data = jwt.decode(
            token,
            settings.jwt_verify_key,
            algorithms=[settings.jwt_algorithm],
        )
        await self.email_verification_repo.create({
            "user_id": user_id,
            "jti": token_data["jti"],
            "expires_at": datetime.fromtimestamp(token_data["exp"], tz=timezone.utc),
        })
        
        # Emit event for email delivery or other side effects
        await dispatcher.emit("auth.user_registered", {"email": email, "token": token, "user_id": user_id})
        
        return token

    async def verify_email(self, token: str) -> models.User:
        """Verifies an email using a token."""
        token_payload = security.verify_email_verification_token(token)
        if not token_payload:
            raise BadRequestError("Invalid or expired verification token")

        email_raw = token_payload.get("sub")
        if not email_raw:
            raise BadRequestError("Invalid token payload")
        email = str(email_raw)
        jti = token_payload.get("jti")
        if not jti:
            raise BadRequestError("Invalid token payload")

        # JTI Blacklist check
        if jti and await is_token_blacklisted(jti):
            raise BadRequestError("Verification link has already been used")

        jti = token_payload.get("jti")
        stored_token = await self.email_verification_repo.get_by_jti(jti)
        
        if not stored_token or stored_token.used:
            raise BadRequestError("Verification link has already been used or is invalid")

        user = await self.users.get_user_by_email(email)
        if not user:
            raise ResourceNotFoundError("User", email)

        if not user.is_verified:
            await self.users.update_user(user, {"is_verified": True})
            await self.email_verification_repo.update(stored_token, {"used": True})

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
        token_data = jwt.decode(
            token,
            settings.jwt_verify_key,
            algorithms=[settings.jwt_algorithm],
        )
        
        await self.password_reset_repo.create({
            "user_id": user.id,
            "jti": token_data["jti"],
            "expires_at": datetime.fromtimestamp(token_data["exp"], tz=timezone.utc),
        })

        # Emit event for email delivery
        await dispatcher.emit("auth.password_reset_requested", {"email": email, "token": token, "user_id": user.id})

    async def bootstrap_admin(self, full_name: str, email: str, password: str) -> models.User:
        """Bootstraps the initial administrator account."""
        if await self.users.has_admin_user():
            from app.core.exceptions import ConflictError
            raise ConflictError("Admin account already exists")

        existing_user = await self.users.get_user_by_email(email)
        if existing_user:
            from app.core.exceptions import ConflictError
            raise ConflictError("Email already registered")

        user_in = {
            "email": email,
            "password": password,
            "full_name": full_name,
            "role": models.enums.UserRole.ADMIN,
            "is_verified": True,
            "is_active": True,
        }
        return await self.users.create_user(user_in)

    async def reset_password(self, token: str, new_password: str) -> models.User:
        """Resets a user password using a valid token."""
        token_payload = security.verify_password_reset_token(token)
        if not token_payload:
            raise BadRequestError("Invalid or expired password reset token")

        email = token_payload.get("sub")
        if not email:
            raise BadRequestError("Invalid reset token subject")
            
        jti = token_payload.get("jti")
        if not jti:
            raise BadRequestError("Invalid reset token identifier")
            
        stored_token = await self.password_reset_repo.get_by_jti(jti)
        
        if not stored_token or stored_token.used:
            raise BadRequestError("Password reset token has already been used")

        user = await self.users.get_user_by_email(email)
        if not user:
            raise ResourceNotFoundError("User", email)

        hashed_password = security.get_password_hash(new_password)
        await self.users.update_user(user, {"password_hash": hashed_password})
        await self.password_reset_repo.update(stored_token, {"used": True})
        
        return user


async def get_auth_service(
    db: AsyncSession = Depends(get_async_db),
    user_service: UserService = Depends(get_user_service)
) -> AuthService:
    """Dependency provider for AuthService."""
    return AuthService(db, user_service)
