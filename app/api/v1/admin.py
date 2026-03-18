from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import RoleChecker, get_db
from app.models.partner_profile import ApprovalStatus
from app.models.user import User, UserRole
from app.schemas.partner_profile import PartnerProfileRead
from app.schemas.user import UserRead
from app.services.admin_service import AdminService
from app.services.partner_service import PartnerService
from app.services.user_service import UserService
from app.schemas.security_log import SecurityLogRead


router = APIRouter()


@router.get("/requests", response_model = List[PartnerProfileRead])
def list_role_requests(
    status: Optional[ApprovalStatus] = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(RoleChecker([UserRole.ADMIN]))
) -> List[PartnerProfileRead]:
    """
    Lists all partner requests, optionally filtered by status.
    Only accessible by administrators.
    """
    return PartnerService.list_requests(db, status)


@router.get("/users/search", response_model = UserRead)
def search_user_by_email(
    email: str,
    db: Session = Depends(get_db),
    current_admin: User = Depends(RoleChecker([UserRole.ADMIN]))
) -> UserRead:
    """
    Searches for a user by their email address.
    Only accessible by administrators.
    """
    user = UserService.get_user_by_email(db, email)

    if not user:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "User not found"
        )

    return user


@router.delete("/users", status_code = status.HTTP_204_NO_CONTENT, response_class = Response)
def delete_user(
    email: str,
    db: Session = Depends(get_db),
    current_admin: User = Depends(RoleChecker([UserRole.ADMIN]))
) -> None:
    """
    Deletes a user by their email address.
    Only accessible by administrators.
    """
    UserService.delete_user_by_email(db, email)
    return None


@router.patch("/approve/{profile_id}", response_model = PartnerProfileRead)
def approve_request(
    profile_id: UUID,
    db: Session = Depends(get_db),
    current_admin: User = Depends(RoleChecker([UserRole.ADMIN]))
) -> PartnerProfileRead:
    """
    Approves a partner request.
    Only accessible by administrators.
    """
    return PartnerService.approve_request(db, profile_id, current_admin.id)


@router.patch("/reject/{profile_id}", response_model = PartnerProfileRead)
def reject_request(
    profile_id: UUID,
    db: Session = Depends(get_db),
    current_admin: User = Depends(RoleChecker([UserRole.ADMIN]))
) -> PartnerProfileRead:
    """
    Rejects a partner request.
    Only accessible by administrators.
    """
    return PartnerService.reject_request(db, profile_id, current_admin.id)


@router.get("/security-logs", response_model = List[SecurityLogRead])
def view_logs(
    db: Session = Depends(get_db),
    current_admin: User = Depends(RoleChecker([UserRole.ADMIN]))
) -> List[SecurityLogRead]:
    """
    Retrieves security logs for administrative review.
    """
    return AdminService.get_security_logs(db)


@router.patch("/users/{user_id}/promote")
def promote(
    user_id: UUID,
    new_role: UserRole,
    db: Session = Depends(get_db),
    current_admin: User = Depends(RoleChecker([UserRole.ADMIN]))
):
    """
    Promotes a user to a new role.
    Only accessible by administrators.
    """
    return UserService.promote_user(db, user_id, new_role)