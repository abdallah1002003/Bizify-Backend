from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db, oauth2_scheme
from app.core import google_client
from app.core.config import settings
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


def _google_redirect_uri() -> str:
    """
    Where Google should send the user back to after consent.
    Must match BOTH the URI used when building the auth URL AND the URI
    sent during the token exchange — Google rejects mismatches.
    Must also be registered in the Google Cloud Console OAuth client.
    """
    return f"{settings.FRONTEND_URL.rstrip('/')}/api/auth/google/callback"


@router.get("/google/url")
def get_google_auth_url() -> dict[str, str]:
    """Return the Google OAuth2 authorization URL."""
    url = google_client.get_google_auth_url(_google_redirect_uri())
    return {"url": url}


@router.post("/google/callback", response_model=Token)
async def google_auth_callback(
    data: GoogleCallbackRequest,
    db: Session = Depends(get_db),
) -> Any:
    """Exchange a Google auth code for a Bizify token."""
    return await AuthService.google_login(
        db, code=data.code, redirect_uri=_google_redirect_uri(),
    )


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
def logout(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> dict[str, str]:
    """Invalidate the current session token."""
    return AuthService.logout(db, token)


@router.post("/verify-otp")
def verify_otp(data: OTPVerify, db: Session = Depends(get_db)) -> dict[str, str]:
    """Verify an account using an emailed OTP."""
    return AuthService.verify_otp(db, data)


@router.post("/resend-verification-otp")
def resend_verification_otp(
    data: OTPResendRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Resend the account verification OTP."""
    return AuthService.resend_verification_otp(db, data)


@router.post("/forgot-password")
def forgot_password(data: OTPResendRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    """Send a password reset code if the email exists."""
    return AuthService.forgot_password(db, data.email)


@router.post("/verify-reset-code")
def verify_reset_code(data: OTPVerify, db: Session = Depends(get_db)) -> dict[str, str]:
    """Verify a password reset code before allowing the user to type a new password."""
    return AuthService.verify_reset_code(db, data.email, data.otp_code)


@router.post("/reset-password")
def reset_password(
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
@router.get("/test-email")
def test_email(email: str) -> dict[str, Any]:
    """
    Diagnostic endpoint for email delivery. Returns the configured provider,
    a config-validation summary, and (if reachable) the result of an actual send.
    Safe to call in production — only the resolved provider is exposed, no secrets.
    """
    from app.core.mail import (
        EmailDeliveryError,
        configured_provider,
        send_otp_email,
        validate_email_config,
    )

    provider = configured_provider()
    ok, message = validate_email_config()
    result: dict[str, Any] = {
        "provider": provider,
        "config_ok": ok,
        "config_message": message,
    }

    if not ok:
        result["sent"] = False
        return result

    try:
        send_otp_email(email, "123456")
        result["sent"] = True
        result["message"] = (
            "Test code 123456 dispatched. Check inbox/spam, or backend logs if EMAIL_DEV_MODE is on."
        )
    except EmailDeliveryError as exc:
        result["sent"] = False
        result["error"] = str(exc)

    return result
