import json
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.user import User, UserRole
from app.models.partner_profile import PartnerType
from app.schemas.partner_profile import PartnerProfileCreate, PartnerProfileRead
from app.schemas.user import UserCreate, UserRead
from app.schemas.user_profile import UserProfileUpdate, UserProfileRead
from app.services.partner_service import PartnerService
from app.services.profile_service import ProfileService
from app.services.user_service import UserService


router = APIRouter()


@router.post(
    "/register",
    response_model = UserRead,
    status_code = status.HTTP_201_CREATED
)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    """
    Registers a new user with the default 'USER' role.
    """
    user_in.role = UserRole.USER
    
    if UserService.get_user_by_email(db, user_in.email):
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Email already registered"
        )
        
    return UserService.create_user(db, user_in)


@router.post(
    "/apply-partner",
    response_model = PartnerProfileRead,
    summary = "Apply to be a Partner",
    description = "Submit a request and upload required documents (PDF/Images).",
    openapi_extra = {
        "requestBody": {
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "required": ["partner_type", "user_id", "files"],
                        "properties": {
                            "partner_type": {
                                "type": "string",
                                "enum": ["mentor", "supplier", "manufacturer"],
                                "description": "Type of partner role"
                            },
                            "user_id": {"type": "string"},
                            "files": {
                                "type": "array",
                                "items": {"type": "string", "format": "binary"},
                                "description": "Upload PDF or image files"
                            },
                            "company_name": {"type": "string", "nullable": True},
                            "description": {"type": "string", "nullable": True},
                            "services_json": {"type": "string", "nullable": True},
                            "experience_json": {"type": "string", "nullable": True}
                        }
                    },
                    "encoding": {
                        "files": {"contentType": "application/pdf, image/*"}
                    }
                }
            }
        }
    }
)
async def apply_to_be_partner(
    partner_type: PartnerType = Form(...),
    user_id: str = Form(...),
    files: List[UploadFile] = File(..., description="Upload PDF or image files"),
    company_name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    services_json: Optional[str] = Form(None),
    experience_json: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PartnerProfileRead:
    """
    Endpoint for users to apply for business roles (mentor, supplier, etc.).
    Requires document uploads for administrative review.
    """
    profile_in = PartnerProfileCreate(
        partner_type = partner_type,
        company_name = company_name,
        description = description,
        services_json = json.loads(services_json) if services_json else None,
        experience_json = json.loads(experience_json) if experience_json else None,
        user_id = UUID(user_id)
    )
    
    return PartnerService.apply_partner(db, current_user, profile_in, files)



@router.post(
    "/profile",
    response_model = UserProfileRead,
    summary = "Update User Profile",
    description = "Updates the user's personal profile and triggers recalculation of dependent analyses."
)
async def update_user_profile(
    profile_in: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UserProfileRead:
    """
    Endpoint to update user profile with validation, change detection, and background tasks.
    """
    updated_profile = ProfileService.update_profile(db, current_user.id, profile_in)
    
    if not updated_profile:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "User profile not found"
        )
    
    return updated_profile
