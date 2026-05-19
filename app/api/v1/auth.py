from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db, oauth2_scheme
from app.core import google_client
from app.core.config import settings
from app.core.limiter import limiter
from app.models.user import User
from app.schemas.user import (
    GoogleCallbackRequest,
    OTPResendRequest,
    OTPVerify,
    PasswordResetRequest,
    Token,
)
from app.services.auth_service import AuthService

router = APIRouter()


@router.get("/google/url")
def get_google_auth_url() -> dict[str, str]:
    """Return the Google OAuth2 authorization URL."""
    redirect_uri = f"{settings.FRONTEND_URL}/"
    url = google_client.get_google_auth_url(redirect_uri)
    return {"url": url}


@router.post("/google/callback", response_model=Token)
@limiter.limit("10/minute")
async def google_auth_callback(
    request: Request,
    data: GoogleCallbackRequest,
    db: Session = Depends(get_db),
) -> Any:
    """Exchange a Google auth code for a Bizify token."""
    redirect_uri = f"{settings.FRONTEND_URL}/"
    return await AuthService.google_login(db, code=data.code, redirect_uri=redirect_uri)


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
def login_access_token(
    request: Request,
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
def logout(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> dict[str, str]:
    """Invalidate the current session token."""
    return AuthService.logout(db, token)


@router.post("/verify-otp")
@limiter.limit("10/minute")
def verify_otp(request: Request, data: OTPVerify, db: Session = Depends(get_db)) -> dict[str, str]:
    """Verify an account using an emailed OTP."""
    return AuthService.verify_otp(db, data)


@router.post("/resend-verification-otp")
@limiter.limit("3/minute")
def resend_verification_otp(
    request: Request,
    data: OTPResendRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Resend the account verification OTP."""
    return AuthService.resend_verification_otp(db, data)


@router.post("/forgot-password")
@limiter.limit("3/minute")
def forgot_password(
    request: Request,
    data: OTPResendRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Send a password reset code if the email exists."""
    return AuthService.forgot_password(db, data.email)


@router.post("/verify-reset-code")
@limiter.limit("10/minute")
def verify_reset_code(
    request: Request,
    data: OTPVerify,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Verify a password reset code before allowing the user to type a new password."""
    return AuthService.verify_reset_code(db, data.email, data.otp_code)


@router.post("/reset-password")
@limiter.limit("5/minute")
def reset_password(
    request: Request,
    data: PasswordResetRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Reset a password using an OTP code."""
    return AuthService.reset_password(db, data.email, data.otp_code, data.new_password)


@router.get("/session-status")
def get_session_status(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
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
def session_ping(current_user: User = Depends(get_current_user)) -> dict[str, str]:
    """Keep the current session active."""
    return {"message": "Session kept alive"}


@router.get("/test-email", include_in_schema=False)
def test_email(email: str, current_user: User = Depends(get_current_user)) -> dict:
    """Internal SMTP connectivity check — admin only, hidden from Swagger."""
    if current_user.role.value != "ADMIN":
        raise HTTPException(status_code=403, detail="Forbidden")
    from app.core.mail import send_otp_email
    try:
        send_otp_email(email, "123456")
        return {"message": "Email sent successfully"}
    except Exception as e:
        return {"error": str(e)}
