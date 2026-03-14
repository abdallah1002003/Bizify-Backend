from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_user,RoleChecker
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserRead
from app.schemas.partner_profile import PartnerProfileCreate, PartnerProfileRead
from app.services import user_service
from app.services.partner_service import PartnerService

router = APIRouter()

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    user_in.role = UserRole.USER
    
    if user_service.get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")
        
    return user_service.create_user(db, user_in)

@router.post("/apply-partner", 
             response_model=PartnerProfileRead,
             summary="Apply to be a Partner",
             description="Submit a request to upgrade your account role. Available partner types: mentor, supplier, manufacturer.")
def apply_to_be_partner(profile_in: PartnerProfileCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return PartnerService.apply_partner(db, current_user, profile_in)

@router.get("/", response_model=list[UserRead])
def read_users(db: Session = Depends(get_db), current_admin: User = Depends(RoleChecker([UserRole.ADMIN]))):
    return user_service.get_all_users(db)
