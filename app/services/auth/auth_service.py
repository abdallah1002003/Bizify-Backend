from datetime import datetime, timedelta, timezone
import logging
from typing import Optional, Tuple
from uuid import UUID

import jwt
from sqlalchemy.ext.asyncio import AsyncSession

import app.models as models
from app.core import security
from app.core.events import dispatcher
from app.core.exceptions import (
    AuthenticationError,
    BadRequestError,
    ConflictError,
    ResourceNotFoundError,
)
from app.core.metrics import active_sessions
from app.core.token_blacklist import blacklist_token, is_token_blacklisted
from app.models.enums import UserRole
from app.repositories.auth_repository import (
    EmailVerificationTokenRepository,
    PasswordResetTokenRepository,
    RefreshTokenRepository,
)
from app.services.base_service import BaseService
from app.services.interfaces import IUserService
from app.services.users.user_service import UserService
from config.settings import settings

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
            await self.refresh_token_repo.create(
                {
                    "user_id": user_id,
                    "jti": token_data["jti"],
                    "expires_at": datetime.fromtimestamp(token_data["exp"], tz=timezone.utc),
                }
            )
        except jwt.PyJWTError as exc:
            logger.error("Failed to persist refresh token: %s", exc)
            raise AuthenticationError("Invalid refresh token") from exc

    async def authenticate_user(self, email: str, password: str) -> Optional[models.User]:
        """Authenticates a user by email and password."""
        user = await self.users.get_user_by_email(email)
        if not user or not security.verify_password(password, user.password_hash):
            return None
        return user

    async def create_tokens(self, user_id: UUID) -> Tuple[str, str]:
        """Creates access and refresh tokens for a user and persists the refresh token."""
        access_token = security.create_access_token(
            user_id,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        refresh_token = security.create_refresh_token(user_id)
        await self._persist_refresh_token(user_id, refresh_token)
        active_sessions.inc()
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
        except (jwt.PyJWTError, ValueError) as exc:
            raise AuthenticationError("Could not validate refresh token") from exc

        user = await self.users.get_user(id=user_id)
        if not user or not user.is_active:
            raise AuthenticationError("Inactive or non-existent user")

        jti_raw = token_data.get("jti")
        if not jti_raw:
            raise AuthenticationError("Invalid token payload")
        jti = str(jti_raw)
        stored_token = await self.refresh_token_repo.get_by_jti(jti)

        if not stored_token or stored_token.revoked:
            raise AuthenticationError("Token has been revoked")

        await self.refresh_token_repo.revoke(jti)
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
            revoked = await self.refresh_token_repo.revoke(jti)
            if revoked:
                active_sessions.dec()
        except jwt.PyJWTError:
            pass

    async def create_verification_token(self, user_id: UUID, email: str) -> str:
        """Creates and persists an email verification token."""
        token = security.create_email_verification_token(email)
        token_data = jwt.decode(
            token,
            settings.jwt_verify_key,
            algorithms=[settings.jwt_algorithm],
        )
        await self.email_verification_repo.create(
            {
                "user_id": user_id,
                "jti": token_data["jti"],
                "expires_at": datetime.fromtimestamp(token_data["exp"], tz=timezone.utc),
            }
        )

        await dispatcher.emit(
            "auth.user_registered",
            {"email": email, "token": token, "user_id": user_id},
        )
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
        jti_raw = token_payload.get("jti")
        if not jti_raw:
            raise BadRequestError("Invalid token payload")
        jti = str(jti_raw)

        if await is_token_blacklisted(jti):
            raise BadRequestError("Verification link has already been used")

        stored_token = await self.email_verification_repo.get_by_jti(jti)
        if not stored_token or stored_token.used:
            raise BadRequestError("Verification link has already been used or is invalid")

        user = await self.users.get_user_by_email(email)
        if not user:
            raise ResourceNotFoundError(resource_type="User", resource_id=email)

        if not user.is_verified:
            await self.users.update_user(user, {"is_verified": True})
            await self.email_verification_repo.mark_used(stored_token)

        exp = token_payload.get("exp")
        if isinstance(exp, (int, float)):
            remaining_ttl = int(exp - datetime.now(timezone.utc).timestamp())
            if remaining_ttl > 0:
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

        await self.password_reset_repo.create(
            {
                "user_id": user.id,
                "jti": token_data["jti"],
                "expires_at": datetime.fromtimestamp(token_data["exp"], tz=timezone.utc),
            }
        )
        await dispatcher.emit(
            "auth.password_reset_requested",
            {"email": email, "token": token, "user_id": user.id},
        )

    async def bootstrap_admin(self, name: str, email: str, password: str) -> models.User:
        """Create the first admin user if none exists and email is free."""
        if await self.users.has_admin_user():
            raise ConflictError(
                message="Admin account already exists",
                conflict_field="role",
                existing_value=UserRole.ADMIN.value,
            )

        if await self.users.get_user_by_email(email):
            raise ConflictError(
                message="Email already registered",
                conflict_field="email",
                existing_value=email,
            )

        return await self.users.create_user(
            obj_in={
                "name": name,
                "email": email,
                "password": password,
                "role": UserRole.ADMIN,
                "is_active": True,
                "is_verified": True,
            }
        )

    async def reset_password(self, token: str, new_password: str) -> models.User:
        """Validate password reset token, update password, and burn the token."""
        token_payload = security.verify_password_reset_token(token)
        if not token_payload:
            raise BadRequestError("Invalid or expired reset token")

        email_claim = token_payload.get("sub")
        if not isinstance(email_claim, str) or not email_claim:
            raise BadRequestError("Invalid reset token subject")

        jti_claim = token_payload.get("jti")
        jti = str(jti_claim) if jti_claim else None
        if not jti:
            raise BadRequestError("Invalid reset token identifier")

        if await is_token_blacklisted(jti):
            raise BadRequestError("Token has already been used")

        stored_token = await self.password_reset_repo.get_by_jti(jti)
        if not stored_token or stored_token.used:
            raise BadRequestError("Token has already been used or is invalid")

        user = await self.users.get_user_by_email(email_claim)
        if not user:
            raise ResourceNotFoundError(resource_type="User", resource_id=email_claim)

        await self.password_reset_repo.mark_used(stored_token, auto_commit=False)
        user = await self.users.update_user(user, {"password": new_password})

        exp_claim = token_payload.get("exp")
        if isinstance(exp_claim, (int, float)):
            remaining_ttl = int(exp_claim - datetime.now(timezone.utc).timestamp())
            if remaining_ttl > 0:
                await blacklist_token(jti, remaining_ttl)

        return user


async def get_auth_service(
    db: AsyncSession,
    user_service: Optional[UserService] = None,
) -> AuthService:
    """Dependency provider for AuthService."""
    user_service = user_service or UserService(db)
    return AuthService(db, user_service)
