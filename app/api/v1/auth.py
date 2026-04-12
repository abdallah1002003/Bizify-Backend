from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db, oauth2_scheme
from app.core import google_client
from app.core.config import settings
from app.models.user import User
from app.schemas.user import GoogleCallbackRequest, OTPResendRequest, OTPVerify, Token
from app.services.auth_service import AuthService

router = APIRouter()


@router.get("/google/url")
def get_google_auth_url() -> Dict[str, str]:
    """Return the Google OAuth2 authorization URL."""
    redirect_uri = f"{settings.FRONTEND_URL}/"
    url = google_client.get_google_auth_url(redirect_uri)
    return {"url": url}


@router.post("/google/callback", response_model=Token)
async def google_auth_callback(
    data: GoogleCallbackRequest,
    db: Session = Depends(get_db),
) -> Any:
    """Exchange a Google auth code for a Bizify token."""
    redirect_uri = f"{settings.FRONTEND_URL}/"
    return await AuthService.google_login(db, code=data.code, redirect_uri=redirect_uri)


@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """Authenticate with email/password and return an access token."""
    user = AuthService.authenticate(
        db,
        email=form_data.username,
        password=form_data.password,
    )
    return AuthService.create_token_response(user)


@router.post("/logout")
def logout(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> Dict[str, str]:
    """Invalidate the current session token."""
    return AuthService.logout(db, token)


@router.post("/verify-otp")
def verify_otp(data: OTPVerify, db: Session = Depends(get_db)) -> Dict[str, str]:
    """Verify an account using an emailed OTP."""
    return AuthService.verify_otp(db, data)


@router.post("/resend-verification-otp")
def resend_verification_otp(
    data: OTPResendRequest,
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Resend the account verification OTP."""
    return AuthService.resend_verification_otp(db, data)


@router.post("/forgot-password")
def forgot_password(email: str, db: Session = Depends(get_db)) -> Dict[str, str]:
    """Send a password reset code if the email exists."""
    return AuthService.forgot_password(db, email)


@router.post("/reset-password")
def reset_password(
    email: str,
    otp_code: str,
    new_password: str,
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Reset a password using an OTP code."""
    return AuthService.reset_password(db, email, otp_code, new_password)


@router.get("/session-status")
def get_session_status(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """Return the current session status and remaining time."""
    now = datetime.now(timezone.utc)
    last_activity = current_user.last_activity

    if last_activity and last_activity.tzinfo is None:
        last_activity = last_activity.replace(tzinfo=timezone.utc)
    else:
        last_activity = last_activity or now

    elapsed = now - last_activity
    remaining = timedelta(minutes=settings.SESSION_TIMEOUT_MINUTES) - elapsed

    return {
        "is_active": True,
        "remaining_minutes": max(0.0, remaining.total_seconds() / 60),
        "warning_threshold": settings.SESSION_WARNING_MINUTES,
    }


@router.post("/ping")
def session_ping(current_user: User = Depends(get_current_user)) -> Dict[str, str]:
    """Keep the current session active."""
    return {"message": "Session kept alive"}
