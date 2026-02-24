from datetime import timedelta, datetime, timezone
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
import logging
from sqlalchemy.orm import Session

import app.models as models
from app.core import dependencies, security
from app.models.enums import UserRole
from app.services.users import user_service
from app.schemas.users.user import UserCreate
from app.services.core.email_service import send_verification_email, send_password_reset_email
from config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class BootstrapAdminRequest(BaseModel):
    name: str = Field(..., max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)


class BootstrapAdminResponse(BaseModel):
    id: UUID
    email: EmailStr
    role: UserRole
    token_type: str
    access_token: str


# ---------------------------------------------------------------------------
# Helper: persist a refresh token in the DB
# ---------------------------------------------------------------------------

def _persist_refresh_token(db: Session, user_id: Any, refresh_token: str) -> None:
    from jose import jwt as jose_jwt
    token_data = jose_jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    db_token = models.RefreshToken(
        user_id=user_id,
        jti=token_data["jti"],
        expires_at=datetime.fromtimestamp(token_data["exp"], tz=timezone.utc),
    )
    db.add(db_token)
    db.commit()


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------

@router.post("/login", response_model=TokenResponse)
def login_access_token(
    db: Session = Depends(dependencies.get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """Authenticate a user and return access + refresh tokens."""
    user = db.query(models.User).filter(models.User.email == form_data.username).first()

    masked_email = (
        f"{form_data.username.split('@')[0][:3]}***@{form_data.username.split('@')[-1]}"
        if "@" in form_data.username
        else "***"
    )

    if not user or not security.verify_password(form_data.password, user.password_hash):
        logger.warning("Failed login attempt for email: %s", masked_email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        logger.warning("Login attempt on inactive account: %s", masked_email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")

    logger.info("Successful login for user: %s", user.id)
    access_token = security.create_access_token(
        user.id, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = security.create_refresh_token(user.id)
    _persist_refresh_token(db, user.id, refresh_token)

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    payload: RefreshTokenRequest,
    db: Session = Depends(dependencies.get_db),
) -> Any:
    from jose import jwt as jose_jwt, JWTError

    try:
        token_data = jose_jwt.decode(
            payload.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        if token_data.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        user_id = token_data.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or non-existent user")

    jti = token_data.get("jti")
    stored_token = db.query(models.RefreshToken).filter(models.RefreshToken.jti == jti).first()
    if not stored_token or stored_token.revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

    stored_token.revoked = True

    access_token = security.create_access_token(
        user.id, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    new_refresh_token = security.create_refresh_token(user.id)
    _persist_refresh_token(db, user.id, new_refresh_token)

    return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}


@router.post(
    "/bootstrap-admin",
    response_model=BootstrapAdminResponse,
    status_code=status.HTTP_201_CREATED,
)
def bootstrap_admin(
    payload: BootstrapAdminRequest,
    db: Session = Depends(dependencies.get_db),
    bootstrap_token: Optional[str] = Header(default=None, alias="X-Bootstrap-Token"),
) -> Any:
    if not settings.ALLOW_ADMIN_BOOTSTRAP:
        raise HTTPException(status_code=403, detail="Admin bootstrap is disabled")

    expected_token = settings.ADMIN_BOOTSTRAP_TOKEN.strip()
    if not expected_token:
        raise HTTPException(status_code=500, detail="ADMIN_BOOTSTRAP_TOKEN is not configured")

    if bootstrap_token != expected_token:
        raise HTTPException(status_code=403, detail="Invalid bootstrap token")

    existing_admin = db.query(models.User).filter(models.User.role == UserRole.ADMIN).first()
    if existing_admin:
        raise HTTPException(status_code=409, detail="Admin account already exists")

    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    admin_user = user_service.create_user(
        db,
        obj_in={
            "name": payload.name,
            "email": payload.email,
            "password_hash": payload.password,
            "role": UserRole.ADMIN,
            "is_active": True,
            "is_verified": True,  # Admin is auto-verified
        },
    )
    access_token = security.create_access_token(
        admin_user.id, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = security.create_refresh_token(admin_user.id)
    _persist_refresh_token(db, admin_user.id, refresh_token)

    return {
        "id": admin_user.id,
        "email": admin_user.email,
        "role": admin_user.role,
        "token_type": "bearer",
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


@router.post("/logout")
def logout(
    payload: RefreshTokenRequest,
    db: Session = Depends(dependencies.get_db),
):
    """Revoke a refresh token (manual logout)."""
    from jose import jwt as jose_jwt, JWTError

    try:
        token_data = jose_jwt.decode(
            payload.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        jti = token_data.get("jti")
        stored = db.query(models.RefreshToken).filter(models.RefreshToken.jti == jti).first()
        if stored:
            stored.revoked = True
            db.commit()
    except JWTError:
        pass  # Silent fail for invalid tokens during logout
    return {"message": "Logged out successfully"}


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    item_in: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(dependencies.get_db),
):
    """
    Register a new user account.

    The account is created with ``is_verified=False``. A verification email
    is dispatched asynchronously so the HTTP response is not blocked by SMTP.
    """
    existing = db.query(models.User).filter(models.User.email == item_in.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    data = item_in.model_dump()
    data["is_active"] = True
    data["is_verified"] = False
    user = user_service.create_user(db, obj_in=data)

    # Create a single-use email verification token and persist it
    token = security.create_email_verification_token(user.email)
    from jose import jwt as jose_jwt
    token_data = jose_jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    db_token = models.EmailVerificationToken(
        user_id=user.id,
        jti=token_data["jti"],
        expires_at=datetime.fromtimestamp(token_data["exp"], tz=timezone.utc),
    )
    db.add(db_token)
    db.commit()

    # Send verification email in the background (non-blocking)
    background_tasks.add_task(send_verification_email, user.email, token)
    logger.info("Queued verification email for user %s", user.id)

    return {"message": "Registered successfully. Please check your email to verify your account.", "id": user.id}


@router.get("/verify-email")
def verify_email(
    token: str = Query(..., description="Email verification JWT from the link in your inbox"),
    db: Session = Depends(dependencies.get_db),
):
    """
    Confirm a user's email address.

    Validates the JWT, ensures the token has not been used, marks the user as
    verified, and invalidates the token so it cannot be reused.
    """
    token_payload = security.verify_email_verification_token(token)
    if not token_payload:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    email = token_payload.get("sub")
    jti = token_payload.get("jti")

    stored_token = (
        db.query(models.EmailVerificationToken)
        .filter(models.EmailVerificationToken.jti == jti)
        .first()
    )
    if not stored_token or stored_token.used:
        raise HTTPException(
            status_code=400, detail="Verification link has already been used or is invalid"
        )

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        return {"message": "Email already verified"}

    user.is_verified = True
    stored_token.used = True
    db.commit()

    logger.info("Email verified for user %s", user.id)
    return {"message": "Email verified successfully. You can now log in."}


@router.post("/forgot-password")
def forgot_password(
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(dependencies.get_db),
):
    """
    Initiate a password reset.

    A one-time reset token is created, persisted to the DB, and emailed to the
    user. Always returns the same message to prevent user enumeration.
    """
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user:
        # Return identical response to avoid revealing whether email exists
        return {"message": "If the account exists, a reset link has been sent"}

    token = security.create_password_reset_token(user.email)

    from jose import jwt as jose_jwt
    token_data = jose_jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    db_token = models.PasswordResetToken(
        user_id=user.id,
        jti=token_data["jti"],
        expires_at=datetime.fromtimestamp(token_data["exp"], tz=timezone.utc),
    )
    db.add(db_token)
    db.commit()

    # Dispatch reset email asynchronously (non-blocking)
    background_tasks.add_task(send_password_reset_email, user.email, token)
    logger.info("Queued password reset email for user %s", user.id)

    return {"message": "If the account exists, a reset link has been sent"}


@router.post("/reset-password")
def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(dependencies.get_db),
):
    """Verify reset token against DB and update the user's password."""
    token_payload = security.verify_password_reset_token(payload.token)
    if not token_payload:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    email = token_payload.get("sub")
    jti = token_payload.get("jti")

    stored_token = (
        db.query(models.PasswordResetToken)
        .filter(models.PasswordResetToken.jti == jti)
        .first()
    )
    if not stored_token or stored_token.used:
        raise HTTPException(status_code=400, detail="Token has already been used or is invalid")

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    stored_token.used = True
    user.password_hash = security.get_password_hash(payload.new_password)
    db.commit()

    return {"message": "Password updated successfully"}
