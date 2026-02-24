from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Optional, Tuple
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import jwt as jose_jwt, JWTError

import app.models as models
from app.db.database import get_db
from app.core import security
from app.services.base_service import BaseService
from app.services.interfaces import IUserService
from app.services.users.user_service import UserService, get_user_service
from app.core.events import dispatcher
from config.settings import settings

logger = logging.getLogger(__name__)


class AuthService(BaseService):
    """Service for handling authentication and token management."""

    def __init__(self, db: Session, user_service: IUserService):
        super().__init__(db)
        self.users = user_service

    def _persist_refresh_token(self, user_id: UUID, refresh_token: str) -> None:
        """Persists a refresh token in the database."""
        try:
            token_data = jose_jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            db_token = models.RefreshToken(
                user_id=user_id,
                jti=token_data["jti"],
                expires_at=datetime.fromtimestamp(token_data["exp"], tz=timezone.utc),
            )
            self.db.add(db_token)
            self.db.commit()
        except JWTError as e:
            logger.error(f"Failed to persist refresh token: {e}")
            raise HTTPException(status_code=401, detail="Invalid refresh token")

    def authenticate_user(self, email: str, password: str) -> Optional[models.User]:
        """Authenticates a user by email and password."""
        user = self.users.get_user_by_email(email)
        if not user or not security.verify_password(password, user.password_hash):
            return None
        return user

    def create_tokens(self, user_id: UUID) -> Tuple[str, str]:
        """Creates access and refresh tokens for a user and persists the refresh token."""
        access_token = security.create_access_token(
            user_id, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        refresh_token = security.create_refresh_token(user_id)
        self._persist_refresh_token(user_id, refresh_token)
        return access_token, refresh_token

    def refresh_access_token(self, refresh_token: str) -> Tuple[str, str]:
        """Refreshes an access token using a valid refresh token."""
        try:
            token_data = jose_jwt.decode(
                refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            if token_data.get("type") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid token type")
            user_id = token_data.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token payload")
        except JWTError:
            raise HTTPException(status_code=401, detail="Could not validate refresh token")

        user = self.users.get_user(id=UUID(user_id))
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Inactive or non-existent user")

        jti = token_data.get("jti")
        stored_token = self.db.query(models.RefreshToken).filter(models.RefreshToken.jti == jti).first()
        if not stored_token or stored_token.revoked:
            raise HTTPException(status_code=401, detail="Token has been revoked")

        # Invalidate old token
        stored_token.revoked = True
        self.db.add(stored_token)
        self.db.commit()

        # Create new tokens
        return self.create_tokens(user.id)

    def revoke_refresh_token(self, refresh_token: str) -> None:
        """Revokes a refresh token."""
        try:
            token_data = jose_jwt.decode(
                refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            jti = token_data.get("jti")
            stored = self.db.query(models.RefreshToken).filter(models.RefreshToken.jti == jti).first()
            if stored:
                stored.revoked = True
                self.db.commit()
        except JWTError:
            pass  # Silent fail for invalid tokens

    async def create_verification_token(self, user_id: UUID, email: str) -> str:
        """Creates and persists an email verification token."""
        token = security.create_email_verification_token(email)
        token_data = jose_jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        db_token = models.EmailVerificationToken(
            user_id=user_id,
            jti=token_data["jti"],
            expires_at=datetime.fromtimestamp(token_data["exp"], tz=timezone.utc),
        )
        self.db.add(db_token)
        self.db.commit()
        
        # Emit event for email delivery or other side effects
        await dispatcher.emit("auth.user_registered", {"email": email, "token": token, "user_id": user_id})
        
        return token

    def verify_email(self, token: str) -> models.User:
        """Verifies an email using a token."""
        token_payload = security.verify_email_verification_token(token)
        if not token_payload:
            raise HTTPException(status_code=400, detail="Invalid or expired verification token")

        email = token_payload.get("sub")
        jti = token_payload.get("jti")

        stored_token = (
            self.db.query(models.EmailVerificationToken)
            .filter(models.EmailVerificationToken.jti == jti)
            .first()
        )
        if not stored_token or stored_token.used:
            raise HTTPException(
                status_code=400, detail="Verification link has already been used or is invalid"
            )

        user = self.users.get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.is_verified:
            user.is_verified = True
            stored_token.used = True
            self.db.add(user)
            self.db.add(stored_token)
            self.db.commit()

        return user

    async def request_password_reset(self, email: str) -> None:
        """Initiates a password reset request and emits an event."""
        user = self.users.get_user_by_email(email)
        if not user:
            return

        token = security.create_password_reset_token(user.email)
        token_data = jose_jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        db_token = models.PasswordResetToken(
            user_id=user.id,
            jti=token_data["jti"],
            expires_at=datetime.fromtimestamp(token_data["exp"], tz=timezone.utc),
        )
        self.db.add(db_token)
        self.db.commit()

        # Emit event for email delivery
        await dispatcher.emit("auth.password_reset_requested", {"email": email, "token": token, "user_id": user.id})


def get_auth_service(
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service)
) -> AuthService:
    """Dependency provider for AuthService."""
    return AuthService(db, user_service)
