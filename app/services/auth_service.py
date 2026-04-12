from datetime import datetime, timedelta, timezone
from typing import Dict

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core import google_client, security
from app.core.config import settings
from app.models.user import User
from app.models.verification import VerificationType
from app.repositories.auth_repo import auth_repo
from app.repositories.profile_repo import profile_repo
from app.repositories.user_repo import user_repo
from app.schemas.user import OTPResendRequest, OTPVerify
from app.services.user_service import UserService


class AuthService:
    """Authentication flows for password, OTP, and Google OAuth."""

    @staticmethod
    async def google_login(db: Session, code: str, redirect_uri: str) -> Dict[str, str]:
        """Authenticate with Google and return an access token response."""
        try:
            access_token = await google_client.exchange_code_for_token(code, redirect_uri)
            user_info = await google_client.get_google_user_info(access_token)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Google authentication failed: {exc}",
            ) from exc

        email = user_info.get("email")
        google_id = user_info.get("id")
        full_name = user_info.get("name")

        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google account did not provide an email address.",
            )

        user = user_repo.get_by_email(db, email)
        if user:
            if not user.google_id:
                user.google_id = google_id
                user_repo.save(db, db_obj=user)

            AuthService._validate_account_state(user)
            return AuthService.create_token_response(user)

        user = user_repo.create(
            db,
            obj_in={
                "email": email,
                "google_id": google_id,
                "full_name": full_name,
                "is_verified": True,
                "is_active": True,
                "password_hash": None,
            },
            commit=False,
            refresh=False,
        )
        profile_repo.create(
            db,
            obj_in={"user_id": user.id},
            commit=False,
            refresh=False,
        )
        db.commit()
        db.refresh(user)

        return AuthService.create_token_response(user)

    @staticmethod
    def authenticate(db: Session, email: str, password: str) -> User:
        """Authenticate a user by email and password."""
        user = UserService.get_user_by_email(db, email=email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        if user.is_locked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Account locked until {user.locked_until}",
            )

        if not user.password_hash or not security.verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)

            user_repo.save(db, db_obj=user)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        AuthService._validate_account_state(user)
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_activity = datetime.now(timezone.utc)
        user_repo.save(db, db_obj=user)
        return user

    @staticmethod
    def _validate_account_state(user: User) -> None:
        """Raise when a user account should not be allowed to log in."""
        if user.is_locked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Account locked until {user.locked_until}",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user",
            )

        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not verified",
            )

    @staticmethod
    def create_token_response(user: User) -> Dict[str, str]:
        """Generate the standard OAuth2 token payload."""
        expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token = security.create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "role": user.role,
            },
            expires_delta=expires,
        )
        return {"access_token": token, "token_type": "bearer"}

    @staticmethod
    def logout(db: Session, token: str) -> Dict[str, str]:
        """Blacklist the current access token."""
        if not auth_repo.is_token_blacklisted(db, token):
            auth_repo.blacklist_token(db, token)

        return {"message": "Successfully logged out"}

    @staticmethod
    def verify_otp(db: Session, data: OTPVerify) -> Dict[str, str]:
        """Validate an account verification OTP."""
        is_verified = UserService.verify_otp_status(
            db,
            email=data.email,
            otp_code=data.otp_code,
        )
        if not is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP",
            )

        return {"message": "Account verified successfully"}

    @staticmethod
    def resend_verification_otp(
        db: Session,
        data: OTPResendRequest,
    ) -> Dict[str, str]:
        """Resend the account verification OTP for an existing user."""
        user = UserService.get_user_by_email(db, email=data.email)
        if not user:
            return {"message": "If this email exists, a verification code has been sent"}

        if user.is_verified:
            return {"message": "Account is already verified"}

        UserService.create_otp(db, user.id, user.email)
        return {"message": "Verification code sent to your email"}

    @staticmethod
    def forgot_password(db: Session, email: str) -> Dict[str, str]:
        """Start the password reset flow."""
        user = UserService.get_user_by_email(db, email=email)
        if not user:
            return {"message": "If this email exists, a reset code has been sent"}

        UserService.create_otp(
            db,
            user.id,
            user.email,
            v_type=VerificationType.PASSWORD_RESET,
        )
        return {"message": "Verification code sent to your email"}

    @staticmethod
    def reset_password(
        db: Session,
        email: str,
        otp_code: str,
        new_password: str,
    ) -> Dict[str, str]:
        """Reset a password after successful OTP verification."""
        is_reset_successful = UserService.reset_password_logic(
            db,
            email,
            otp_code,
            new_password,
        )
        if not is_reset_successful:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP",
            )

        return {"message": "Password reset successfully"}
