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
from config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


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
    
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "refresh_token": security.create_refresh_token(user.id),
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
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "refresh_token": security.create_refresh_token(user.id),
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
    access_token = security.create_access_token(
        admin_user.id, expires_delta=access_token_expires
    )
    return {
        "id": admin_user.id,
        "email": admin_user.email,
        "role": admin_user.role,
        "token_type": "bearer",
        "access_token": access_token,
    }
