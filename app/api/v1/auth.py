from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db, oauth2_scheme
from app.core.config import settings
from app.models.user import User
from app.schemas.user import OTPResendRequest, OTPVerify, Token
from app.services.auth_service import AuthService


router = APIRouter()


@router.post("/login", response_model = Token)
def login_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, retrieve an access token for future requests.
    """
    user = AuthService.authenticate(
        db,
        email = form_data.username,
        password = form_data.password
    )
    
    return AuthService.create_token_response(user)


@router.post("/logout")
def logout(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> Dict[str, str]:
    """
    Invalidates the current session token.
    """
    return AuthService.logout(db, token)


@router.post("/verify-otp")
def verify_otp(data: OTPVerify, db: Session = Depends(get_db)) -> Dict[str, str]:
    """
    Verifies the account using a 6-digit OTP code sent to email.
    """
    return AuthService.verify_otp(db, data)


@router.post("/resend-verification-otp")
def resend_verification_otp(
    data: OTPResendRequest,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Resends the account verification OTP for users who have not verified yet.
    """
    return AuthService.resend_verification_otp(db, data)
    

@router.post("/forgot-password")
def forgot_password(email: str, db: Session = Depends(get_db)) -> Dict[str, str]:
    """
    Sends a password reset code if the email address exists.
    """
    return AuthService.forgot_password(db, email)
    

@router.post("/reset-password")
def reset_password(
    email: str,
    otp_code: str,
    new_password: str,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Resets the password using a reset code and new password.
    """
    return AuthService.reset_password(db, email, otp_code, new_password)


@router.get("/session-status")
def get_session_status(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Retrieves the current session's remaining time and status.
    """
    now = datetime.now(timezone.utc)
    last_act = current_user.last_activity
    
    if last_act and last_act.tzinfo is None:
        last_act = last_act.replace(tzinfo=timezone.utc)
    else:
        last_act = last_act or now
        
    elapsed = now - last_act
    remaining = timedelta(minutes=settings.SESSION_TIMEOUT_MINUTES) - elapsed
    
    return {
        "is_active": True,
        "remaining_minutes": max(0.0, remaining.total_seconds() / 60),
        "warning_threshold": settings.SESSION_WARNING_MINUTES
    }


@router.post("/ping")
def session_ping(current_user: User = Depends(get_current_user)) -> Dict[str, str]:
    """
    Keeps the session alive by updating the last activity timestamp.
    """
    return {"message": "Session kept alive"}
