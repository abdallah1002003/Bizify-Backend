from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.models.token_blacklist import TokenBlacklist
from app.models.user import User
from app.models.verification import VerificationType
from app.schemas.user import OTPResendRequest, OTPVerify
from app.services.user_service import UserService


class AuthService:
    """
    Service class for handling authentication and authorization logic.
    Manages session state, tokens, and multi-factor verification flows.
    """

    @staticmethod
    def authenticate(db: Session, email: str, password: str) -> User:
        """
        Authenticates a user by email and password.
        Implements brute-force protection through failed attempt tracking and account locking.
        """
        user = UserService.get_user_by_email(db, email = email)
        
        if not user:
            raise HTTPException(
                status_code = status.HTTP_401_UNAUTHORIZED,
                detail = "Incorrect email or password"
            )

        if user.is_locked:
            raise HTTPException(
                status_code = status.HTTP_401_UNAUTHORIZED,
                detail = f"Account locked until {user.locked_until}"
            )

        if not security.verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            
            if user.failed_login_attempts >= 5:
                # Lock the account for 15 minutes after 5 consecutive failures
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes = 15)
                
            db.commit()
            
            raise HTTPException(
                status_code = status.HTTP_401_UNAUTHORIZED,
                detail = "Incorrect email or password"
            )

        # Reset security counters on successful authentication
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_activity = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(user)
        
        if not user.is_active:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = "Inactive user"
            )
            
        if not user.is_verified:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = "User not verified"
            )
            
        return user

    @staticmethod
    def create_token_response(user: User) -> Dict[str, str]:
        """
        Generates a standard OAuth2 access token response for a verified user.
        """
        expires = timedelta(minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        token = security.create_access_token(
            data = {
                "sub": str(user.id),
                "email": user.email,
                "role": user.role
            },
            expires_delta = expires
        )
        
        return {
            "access_token": token, 
            "token_type": "bearer"
        }

    @staticmethod
    def logout(db: Session, token: str) -> Dict[str, str]:
        """
        Invalidates a JWT by adding it to the server-side blacklist.
        """
        is_blacklisted = db.query(TokenBlacklist).filter(TokenBlacklist.token == token).first()
        
        if not is_blacklisted:
            db.add(TokenBlacklist(token = token))
            db.commit()
            
        return {"message": "Successfully logged out"}
    
    @staticmethod
    def verify_otp(db: Session, data: OTPVerify) -> Dict[str, str]:
        """
        Validates an OTP code for user account verification.
        """
        is_verified = UserService.verify_otp_status(
            db,
            email = data.email,
            otp_code = data.otp_code
        )
        
        if not is_verified:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = "Invalid or expired OTP"
            )
            
        return {"message": "Account verified successfully"}

    @staticmethod
    def resend_verification_otp(
        db: Session,
        data: OTPResendRequest
    ) -> Dict[str, str]:
        """
        Resends the account verification OTP for an existing unverified user.
        """
        user = UserService.get_user_by_email(db, email = data.email)

        if not user:
            return {"message": "If this email exists, a verification code has been sent"}

        if user.is_verified:
            return {"message": "Account is already verified"}

        UserService.create_otp(db, user.id, user.email)

        return {"message": "Verification code sent to your email"}

    @staticmethod
    def forgot_password(db: Session, email: str) -> Dict[str, str]:
        """
        Initiates the password recovery flow by issuing a specialized OTP.
        """
        user = UserService.get_user_by_email(db, email = email)
        
        if not user:
            # Masking result for security to prevent user enumeration
            return {"message": "If this email exists, a reset code has been sent"}
            
        UserService.create_otp(
            db,
            user.id,
            user.email,
            v_type = VerificationType.PASSWORD_RESET
        )
        
        return {"message": "Verification code sent to your email"}

    @staticmethod
    def reset_password(
        db: Session,
        email: str,
        otp_code: str,
        new_password: str
    ) -> Dict[str, str]:
        """
        Executes a password reset once the recovery OTP has been validated.
        """
        is_reset_successful = UserService.reset_password_logic(db, email, otp_code, new_password)
        
        if not is_reset_successful:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = "Invalid or expired OTP"
            )
            
        return {"message": "Password reset successfully"}
