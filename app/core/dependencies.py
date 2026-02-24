"""
Authentication and authorization dependencies for FastAPI routes.

Provides:
    get_current_user           — decode JWT and return User
    get_current_active_user    — active + email-verified guard
    require_roles(*roles)      — factory: returns a Depends that enforces role membership
    require_admin              — pre-built Depends: ADMIN only
    is_admin_or_self           — helper used by routes that allow admin OR same-user access
"""

from typing import Callable
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db.database import get_db
from config.settings import settings
import app.models as models
from app.models.enums import UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> models.User:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_verify_key,       # ← uses public key (RS256) or secret (HS256)
            algorithms=[settings.jwt_algorithm],
        )

        if payload.get("type") == "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token cannot be used as an access token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except (JWTError, ValidationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user_model = db.query(models.User).filter(models.User.id == user_id).first()
    if not user_model:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_model


def get_current_active_user(current_user: models.User = Depends(get_current_user)) -> models.User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")

    # Skip email verification check in test environment
    if settings.APP_ENV != "test" and not current_user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified")

    return current_user


# ---------------------------------------------------------------------------
# RBAC helpers
# ---------------------------------------------------------------------------

def require_roles(*allowed_roles: UserRole) -> Callable:
    """
    Dependency factory that enforces role membership.

    Usage::

        @router.delete("/{id}", dependencies=[Depends(require_roles(UserRole.ADMIN))])
        def delete_user(...):
            ...

        # Multiple roles (any match):
        @router.get("/", dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.SUPPORT))])
        def list_users(...):
            ...
    """
    def _check(current_user: models.User = Depends(get_current_active_user)) -> models.User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {', '.join(r.value for r in allowed_roles)}",
            )
        return current_user

    return _check


# Pre-built shortcut for the most common case
require_admin: Callable = require_roles(UserRole.ADMIN)


def is_admin_or_self(current_user: models.User, target_user_id: UUID) -> bool:
    """Return True if the user is an admin or is accessing their own resource."""
    return current_user.role == UserRole.ADMIN or current_user.id == target_user_id


def require_admin_or_self(current_user: models.User, target_user_id: UUID) -> None:
    """Raise 403 unless the user is an admin or accessing their own resource."""
    if not is_admin_or_self(current_user, target_user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
