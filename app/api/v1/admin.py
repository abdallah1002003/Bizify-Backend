from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, RoleChecker
from app.models.user import User, UserRole
from app.schemas.partner_profile import PartnerProfileRead
from app.schemas.user import UserRead
from app.services.partner_service import PartnerService
from app.services import user_service
from app.services.admin_service import AdminService
from uuid import UUID
from typing import Optional, List
from app.models.partner_profile import ApprovalStatus

router = APIRouter()

@router.get("/requests", response_model=List[PartnerProfileRead])
def list_role_requests(status: Optional[ApprovalStatus] = None, db: Session = Depends(get_db), current_admin: User = Depends(RoleChecker([UserRole.ADMIN]))):
    return PartnerService.list_requests(db, status)

@router.get("/users/search", response_model=UserRead)
def search_user_by_email(email: str, db: Session = Depends(get_db), current_admin: User = Depends(RoleChecker([UserRole.ADMIN]))):
    user = user_service.get_user_by_email(db, email)
    if not user: raise HTTPException(status_code=404, detail="User not found")
    return user

@router.delete("/users", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(email: str, db: Session = Depends(get_db), current_admin: User = Depends(RoleChecker([UserRole.ADMIN]))):
    user_service.delete_user_by_email(db, email)
    return None

@router.patch("/approve/{profile_id}", response_model=PartnerProfileRead)
def approve_request(profile_id: UUID, db: Session = Depends(get_db), current_admin: User = Depends(RoleChecker([UserRole.ADMIN]))):
    return PartnerService.approve_request(db, profile_id, current_admin.id)

@router.patch("/reject/{profile_id}", response_model=PartnerProfileRead)
def reject_request(profile_id: UUID, db: Session = Depends(get_db), current_admin: User = Depends(RoleChecker([UserRole.ADMIN]))):
    return PartnerService.reject_request(db, profile_id, current_admin.id)

@router.get("/security-logs")
def view_logs(db: Session = Depends(get_db), current_admin: User = Depends(RoleChecker([UserRole.ADMIN]))):
    return AdminService.get_security_logs(db)

@router.patch("/users/{user_id}/promote")
def promote(user_id: UUID, new_role: UserRole, db: Session = Depends(get_db), current_admin: User = Depends(RoleChecker([UserRole.ADMIN]))):
    return user_service.promote_user(db, user_id, new_role)