from datetime import timedelta
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
import logging
from sqlalchemy.orm import Session

import app.models as models
from app.core import dependencies, security
from app.models.enums import UserRole
from app.services.users import user_service
from app.schemas.users.user import UserCreate
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


@router.post("/login", response_model=TokenResponse)
def login_access_token(
    db: Session = Depends(dependencies.get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    # OAuth2 specifies 'username', we map it to 'email'
    user = db.query(models.User).filter(models.User.email == form_data.username).first()

    masked_email = f"{form_data.username.split('@')[0][:3]}***@{form_data.username.split('@')[-1]}" if "@" in form_data.username else "***"

    if not user or not security.verify_password(form_data.password, user.password_hash):
        logger.warning(f"Failed login attempt for email: {masked_email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        logger.warning(f"Login attempt on inactive account: {masked_email}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")

    logger.info(f"Successful login for user: {user.id}")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    access_token = security.create_access_token(user.id, expires_delta=access_token_expires)
    refresh_token = security.create_refresh_token(user.id)
    
    # Persist refresh token in DB
    from jose import jwt
    from datetime import datetime, timezone
    token_data = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    db_token = models.RefreshToken(
        user_id=user.id,
        jti=token_data["jti"],
        expires_at=datetime.fromtimestamp(token_data["exp"], tz=timezone.utc)
    )
    db.add(db_token)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    payload: RefreshTokenRequest,
    db: Session = Depends(dependencies.get_db),
) -> Any:
    from jose import jwt, JWTError
    try:
        token_data = jwt.decode(payload.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
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
    
    # Check if token is revoked in DB
    jti = token_data.get("jti")
    stored_token = db.query(models.RefreshToken).filter(models.RefreshToken.jti == jti).first()
    if not stored_token or stored_token.revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
        
    # Rotate token: revoke old one, create new one
    stored_token.revoked = True
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(user.id, expires_delta=access_token_expires)
    new_refresh_token = security.create_refresh_token(user.id)
    
    from datetime import datetime, timezone
    new_token_data = jwt.decode(new_refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    new_db_token = models.RefreshToken(
        user_id=user.id,
        jti=new_token_data["jti"],
        expires_at=datetime.fromtimestamp(new_token_data["exp"], tz=timezone.utc)
    )
    db.add(new_db_token)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


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
            "is_verified": True,
        },
    )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(admin_user.id, expires_delta=access_token_expires)
    refresh_token = security.create_refresh_token(admin_user.id)
    
    # Persist refresh token in DB
    from jose import jwt
    from datetime import datetime, timezone
    token_data = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    db_token = models.RefreshToken(
        user_id=admin_user.id,
        jti=token_data["jti"],
        expires_at=datetime.fromtimestamp(token_data["exp"], tz=timezone.utc)
    )
    db.add(db_token)
    db.commit()

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
    from jose import jwt, JWTError
    from app.models.users.user import RefreshToken
    try:
        token_data = jwt.decode(payload.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        jti = token_data.get("jti")
        stored = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
        if stored:
            stored.revoked = True
            db.commit()
    except JWTError:
        pass  # Silent fail for invalid tokens during logout
    return {"message": "Logged out successfully"}


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    item_in: UserCreate,
    db: Session = Depends(dependencies.get_db),
):
    """Public registration for new users (unverified by default)."""
    existing = db.query(models.User).filter(models.User.email == item_in.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    
    data = item_in.model_dump()
    data["is_active"] = True
    data["is_verified"] = False
    user = user_service.create_user(db, obj_in=data)
    return {"message": "Registered successfully, awaiting verification", "id": user.id}


@router.post("/forgot-password")
def forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(dependencies.get_db),
):
    """Generate a password reset token and persist it in DB."""
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user:
        return {"message": "If the account exists, a reset link has been sent"}
    
    token = security.create_password_reset_token(user.email)
    
    # Store token in DB for one-time use tracking
    from datetime import datetime, timezone
    from jose import jwt
    token_data = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    
    db_token = models.PasswordResetToken(
        user_id=user.id,
        jti=token_data["jti"],
        expires_at=datetime.fromtimestamp(token_data["exp"], tz=timezone.utc)
    )
    db.add(db_token)
    db.commit()
    
    # In a real app, send the email here. LOGGING TOKEN IS REMOVED FOR SECURITY.
    return {"message": "If the account exists, a reset link has been sent"}


@router.post("/reset-password")
def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(dependencies.get_db),
):
    """Verify reset token against DB revocation and update password."""
    token_payload = security.verify_password_reset_token(payload.token)
    if not token_payload:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    email = token_payload.get("sub")
    jti = token_payload.get("jti")
    
    # Check if token was already used in DB
    stored_token = db.query(models.PasswordResetToken).filter(models.PasswordResetToken.jti == jti).first()
    if not stored_token or stored_token.used:
        raise HTTPException(status_code=400, detail="Token has already been used or is invalid")
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Mark token as used
    stored_token.used = True
    
    # Update password
    user.password_hash = security.get_password_hash(payload.new_password)
    db.commit()
    
    return {"message": "Password updated successfully"}

