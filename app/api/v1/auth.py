from datetime import timedelta, datetime, timezone
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
import logging
from jose import jwt as jose_jwt, JWTError
from sqlalchemy.orm import Session

import app.models as models
from app.core import dependencies, security
from app.models.enums import UserRole
from app.services.users.user_service import UserService, get_user_service
from app.services.auth.auth_service import AuthService, get_auth_service
from app.schemas.users.user import UserCreate
from app.services.core.email_service import send_verification_email, send_password_reset_email
from app.core.token_blacklist import blacklist_token
from config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


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
# Auth endpoints
# ---------------------------------------------------------------------------

@router.post("/login", response_model=TokenResponse)
def login_access_token(
    auth_service: AuthService = Depends(get_auth_service),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """Authenticate a user and return access + refresh tokens."""
    user = auth_service.authenticate_user(form_data.username, form_data.password)

    if not user:
        masked_email = (
            f"{form_data.username.split('@')[0][:3]}***@{form_data.username.split('@')[-1]}"
            if "@" in form_data.username
            else "***"
        )
        logger.warning("Failed login attempt for email: %s", masked_email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")

    logger.info("Successful login for user: %s", user.id)
    access_token, refresh_token = auth_service.create_tokens(user.id)

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    payload: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> Any:
    access_token, refresh_token = auth_service.refresh_access_token(payload.refresh_token)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post(
    "/bootstrap-admin",
    response_model=BootstrapAdminResponse,
    status_code=status.HTTP_201_CREATED,
)
def bootstrap_admin(
    payload: BootstrapAdminRequest,
    auth_service: AuthService = Depends(get_auth_service),
    bootstrap_token: Optional[str] = Header(default=None, alias="X-Bootstrap-Token"),
) -> Any:
    if not settings.ALLOW_ADMIN_BOOTSTRAP:
        raise HTTPException(status_code=403, detail="Admin bootstrap is disabled")

    expected_token = settings.ADMIN_BOOTSTRAP_TOKEN.strip()
    if not expected_token:
        raise HTTPException(status_code=500, detail="ADMIN_BOOTSTRAP_TOKEN is not configured")

    if bootstrap_token != expected_token:
        raise HTTPException(status_code=403, detail="Invalid bootstrap token")

    existing_admin = auth_service.db.query(models.User).filter(models.User.role == UserRole.ADMIN).first()
    if existing_admin:
        raise HTTPException(status_code=409, detail="Admin account already exists")

    if auth_service.users.get_user_by_email(payload.email):
        raise HTTPException(status_code=409, detail="Email already registered")

    admin_user = auth_service.users.create_user(
        obj_in={
            "name": payload.name,
            "email": payload.email,
            "password": payload.password,
            "role": UserRole.ADMIN,
            "is_active": True,
            "is_verified": True,
        },
    )
    access_token, refresh_token = auth_service.create_tokens(admin_user.id)

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
    request: Request,
    payload: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Revoke refresh token and blacklist the current access token."""
    # 1. Revoke refresh token in DB
    auth_service.revoke_refresh_token(payload.refresh_token)

    # 2. Blacklist the access token so it cannot be reused until expiry
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        access_token = auth_header.split(" ", 1)[1]
        try:
            token_data = jose_jwt.decode(
                access_token,
                settings.jwt_verify_key,
                algorithms=[settings.jwt_algorithm],
            )
            jti = token_data.get("jti")
            exp = token_data.get("exp")
            if jti and exp:
                remaining_ttl = int(exp - datetime.now(timezone.utc).timestamp())
                blacklist_token(jti, remaining_ttl)
        except JWTError:
            pass  # Token already invalid — nothing to blacklist

    return {"message": "Logged out successfully"}


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    item_in: UserCreate,
    background_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register a new user account and send verification email."""
    existing = auth_service.users.get_user_by_email(item_in.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    data = item_in.model_dump()
    data["is_active"] = True
    data["is_verified"] = False
    user = auth_service.users.create_user(obj_in=data)

    # Create and persist verification token (emits event)
    await auth_service.create_verification_token(user.id, user.email)

    return {"message": "Registered successfully. Please check your email to verify your account.", "id": user.id}


@router.get("/verify-email")
def verify_email(
    token: str = Query(..., description="Email verification JWT"),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Confirm a user's email address."""
    user = auth_service.verify_email(token)
    logger.info("Email verified for user %s", user.id)
    return {"message": "Email verified successfully. You can now log in."}


@router.post("/forgot-password")
async def forgot_password(
    payload: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Initiate a password reset."""
    await auth_service.request_password_reset(payload.email)
    return {"message": "If the account exists, a reset link has been sent"}


@router.post("/reset-password")
def reset_password(
    payload: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Verify reset token against DB and update the user's password."""
    token_payload = security.verify_password_reset_token(payload.token)
    if not token_payload:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    email = token_payload.get("sub")
    jti = token_payload.get("jti")

    stored_token = (
        auth_service.db.query(models.PasswordResetToken)
        .filter(models.PasswordResetToken.jti == jti)
        .first()
    )
    if not stored_token or stored_token.used:
        raise HTTPException(status_code=400, detail="Token has already been used or is invalid")

    user = auth_service.users.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    stored_token.used = True
    user.password_hash = security.get_password_hash(payload.new_password)
    auth_service.db.add(user)
    auth_service.db.add(stored_token)
    auth_service.db.commit()

    return {"message": "Password updated successfully"}
