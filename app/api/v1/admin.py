import logging
import os
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import RoleChecker, get_db
from app.models.partner_profile import ApprovalStatus, PartnerProfile, PartnerType
from app.models.platform_setting import PlatformSetting
from app.models.user import User, UserRole
from app.repositories.partner_repo import partner_repo
from app.repositories.user_repo import user_repo
from app.schemas.partner_profile import PartnerProfileRead
from app.schemas.security_log import SecurityLogRead
from app.schemas.user import UserRead
from app.services.admin_service import AdminService
from app.services.partner_service import PartnerService
from app.services.user_service import UserService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/requests", response_model=list[PartnerProfileRead])
def list_role_requests(
    status: Optional[ApprovalStatus] = None,
    db: Session = Depends(get_db),
    _current_admin: User = Depends(RoleChecker([UserRole.ADMIN])),
) -> list[PartnerProfileRead]:
    """List partner requests, optionally filtered by status."""
    return PartnerService.list_requests(db, status)


@router.get("/users/search", response_model=UserRead)
def search_user_by_email(
    email: str,
    db: Session = Depends(get_db),
    _current_admin: User = Depends(RoleChecker([UserRole.ADMIN])),
) -> UserRead:
    """Search for a user by email address."""
    user = UserService.get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.delete("/users", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_user(
    email: str,
    db: Session = Depends(get_db),
    _current_admin: User = Depends(RoleChecker([UserRole.ADMIN])),
) -> None:
    """Delete a user by email address."""
    UserService.delete_user_by_email(db, email)
    return None


class BulkAction(BaseModel):
    ids: list[UUID]
    action: str  # "approve" | "reject"


@router.post("/requests/bulk", response_model=dict)
def bulk_action_requests(
    payload: BulkAction,
    db: Session = Depends(get_db),
    current_admin: User = Depends(RoleChecker([UserRole.ADMIN])),
) -> dict:
    """Bulk approve or reject partner requests in a single transaction."""
    if payload.action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="action must be 'approve' or 'reject'")

    # payload.ids are already UUID objects (Pydantic coerces them)
    profiles = (
        db.query(PartnerProfile)
        .filter(PartnerProfile.id.in_(payload.ids))
        .all()
    )

    new_status = ApprovalStatus.APPROVED if payload.action == "approve" else ApprovalStatus.REJECTED
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

    # Build a map of user_id (UUID) → partner_type for role promotion (approve only)
    user_type_map: dict[UUID, PartnerType] = {}
    for profile in profiles:
        profile.approval_status = new_status
        profile.approved_by = current_admin.id
        profile.approved_at = now
        if payload.action == "approve" and profile.user_id and profile.partner_type:
            user_type_map[profile.user_id] = profile.partner_type

    if payload.action == "approve" and user_type_map:
        users = db.query(User).filter(User.id.in_(list(user_type_map.keys()))).all()
        for user in users:
            ptype = user_type_map.get(user.id)
            if ptype:
                try:
                    user.role = UserRole(ptype.value)
                except ValueError:
                    pass

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error("Bulk %s failed: %s", payload.action, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Bulk {payload.action} failed") from exc

    return {"affected": len(profiles)}


@router.patch("/approve/{profile_id}", response_model=PartnerProfileRead)
def approve_request(
    profile_id: UUID,
    db: Session = Depends(get_db),
    current_admin: User = Depends(RoleChecker([UserRole.ADMIN])),
) -> PartnerProfileRead:
    """Approve a partner request."""
    return PartnerService.approve_request(db, profile_id, current_admin.id)


@router.patch("/reject/{profile_id}", response_model=PartnerProfileRead)
def reject_request(
    profile_id: UUID,
    db: Session = Depends(get_db),
    current_admin: User = Depends(RoleChecker([UserRole.ADMIN])),
) -> PartnerProfileRead:
    """Reject a partner request."""
    return PartnerService.reject_request(db, profile_id, current_admin.id)


@router.get("/security-logs", response_model=list[SecurityLogRead])
def view_logs(
    db: Session = Depends(get_db),
    _current_admin: User = Depends(RoleChecker([UserRole.ADMIN])),
) -> list[SecurityLogRead]:
    """Return security logs for administrative review."""
    return AdminService.get_security_logs(db)


@router.patch("/users/{user_id}/promote", response_model=UserRead)
def promote(
    user_id: UUID,
    new_role: UserRole,
    db: Session = Depends(get_db),
    _current_admin: User = Depends(RoleChecker([UserRole.ADMIN])),
) -> UserRead:
    """Promote a user to a new role."""
    return UserService.promote_user(db, user_id, new_role)


@router.get("/users", response_model=list[UserRead])
def get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _current_admin: User = Depends(RoleChecker([UserRole.ADMIN])),
) -> list[UserRead]:
    """Return a paginated list of users."""
    try:
        rows = user_repo.get_multi(db, skip=skip, limit=limit)
    except Exception as exc:
        logger.error("Failed to query users: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch users. Please try again.",
        ) from exc

    # Validate each row individually so one bad record never breaks the whole list.
    result: list[UserRead] = []
    for row in rows:
        try:
            result.append(UserRead.model_validate(row))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Skipping user id=%s from admin list — validation error: %s", getattr(row, "id", "?"), exc)
    return result


@router.get("/users/{user_id}", response_model=UserRead)
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    _current_admin: User = Depends(RoleChecker([UserRole.ADMIN])),
) -> UserRead:
    """Return a single user by ID."""
    user = user_repo.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/stats", response_model=dict[str, Any])
def get_dashboard_stats(
    db: Session = Depends(get_db),
    _current_admin: User = Depends(RoleChecker([UserRole.ADMIN])),
) -> dict[str, Any]:
    """Return aggregate dashboard statistics."""
    return AdminService.get_dashboard_stats(db=db)


@router.patch("/users/{user_id}/suspend", response_model=UserRead)
def suspend_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_admin: User = Depends(RoleChecker([UserRole.ADMIN])),
) -> UserRead:
    """Suspend a user and invalidate active sessions."""
    return AdminService.suspend_user(db=db, admin_id=current_admin.id, user_id=user_id)


@router.patch("/users/{user_id}/unsuspend", response_model=UserRead)
def unsuspend_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_admin: User = Depends(RoleChecker([UserRole.ADMIN])),
) -> UserRead:
    """Reinstate a suspended user."""
    return AdminService.unsuspend_user(
        db=db, admin_id=current_admin.id, user_id=user_id
    )


_EDITABLE_SETTINGS = {
    "allow_registration",
    "require_email_verification",
    "max_login_attempts",
    "session_timeout_minutes",
    "debug_mode",
}


def _load_platform_config(db: Session) -> dict[str, Any]:
    """Build the platform config dict, giving DB overrides priority over env vars."""
    defaults: dict[str, Any] = {
        "session_timeout_minutes": int(os.getenv("SESSION_TIMEOUT_MINUTES", "240")),
        "jwt_expire_minutes": int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080")),
        "environment": os.getenv("ENVIRONMENT", os.getenv("ENV", "production")),
        "debug_mode": os.getenv("DEBUG", "false").lower() == "true",
        "allow_registration": os.getenv("ALLOW_REGISTRATION", "true").lower() == "true",
        "require_email_verification": os.getenv("REQUIRE_EMAIL_VERIFICATION", "true").lower() == "true",
        "max_login_attempts": int(os.getenv("MAX_LOGIN_ATTEMPTS", "5")),
        "backend_version": os.getenv("APP_VERSION", "1.0.0"),
    }
    rows = db.query(PlatformSetting).all()
    for row in rows:
        if row.key in defaults:
            raw = row.value
            existing = defaults[row.key]
            if isinstance(existing, bool):
                defaults[row.key] = raw.lower() in ("true", "1", "yes")
            elif isinstance(existing, int):
                try:
                    defaults[row.key] = int(raw)
                except ValueError:
                    pass
            else:
                defaults[row.key] = raw
    return defaults


class PlatformConfigUpdate(BaseModel):
    allow_registration: Optional[bool] = None
    require_email_verification: Optional[bool] = None
    max_login_attempts: Optional[int] = None
    session_timeout_minutes: Optional[int] = None
    debug_mode: Optional[bool] = None


@router.get("/platform-config", response_model=dict[str, Any])
def get_platform_config(
    db: Session = Depends(get_db),
    _current_admin: User = Depends(RoleChecker([UserRole.ADMIN])),
) -> dict[str, Any]:
    """Return platform configuration (DB overrides take priority over env vars)."""
    return _load_platform_config(db)


@router.patch("/platform-config", response_model=dict[str, Any])
def update_platform_config(
    payload: PlatformConfigUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(RoleChecker([UserRole.ADMIN])),
) -> dict[str, Any]:
    """Persist one or more editable settings to the database."""
    updates = payload.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No settings provided")

    for key, value in updates.items():
        if key not in _EDITABLE_SETTINGS:
            raise HTTPException(status_code=400, detail=f"Setting '{key}' is not editable")

        row = db.query(PlatformSetting).filter(PlatformSetting.key == key).first()
        str_value = str(value).lower() if isinstance(value, bool) else str(value)
        if row:
            row.value = str_value
            row.updated_by = str(current_admin.email)
        else:
            db.add(PlatformSetting(key=key, value=str_value, updated_by=str(current_admin.email)))

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error("Failed to update platform config: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save settings") from exc

    return _load_platform_config(db)
