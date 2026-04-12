from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import RoleChecker, get_db
from app.models.partner_profile import ApprovalStatus
from app.models.user import User, UserRole
from app.repositories.user_repo import user_repo
from app.schemas.partner_profile import PartnerProfileRead
from app.schemas.security_log import SecurityLogRead
from app.schemas.user import UserRead
from app.services.admin_service import AdminService
from app.services.partner_service import PartnerService
from app.services.user_service import UserService

router = APIRouter()


@router.get("/requests", response_model=List[PartnerProfileRead])
def list_role_requests(
    status: Optional[ApprovalStatus] = None,
    db: Session = Depends(get_db),
    _current_admin: User = Depends(RoleChecker([UserRole.ADMIN])),
) -> List[PartnerProfileRead]:
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


@router.get("/security-logs", response_model=List[SecurityLogRead])
def view_logs(
    db: Session = Depends(get_db),
    _current_admin: User = Depends(RoleChecker([UserRole.ADMIN])),
) -> List[SecurityLogRead]:
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


@router.get("/users", response_model=List[UserRead])
def get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _current_admin: User = Depends(RoleChecker([UserRole.ADMIN])),
) -> List[UserRead]:
    """Return a paginated list of users."""
    return user_repo.get_multi(db, skip=skip, limit=limit)


@router.get("/stats", response_model=Dict[str, Any])
def get_dashboard_stats(
    db: Session = Depends(get_db),
    _current_admin: User = Depends(RoleChecker([UserRole.ADMIN])),
) -> Dict[str, Any]:
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
