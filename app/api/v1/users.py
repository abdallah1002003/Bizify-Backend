import json
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.partner_profile import PartnerType
from app.models.user import User, UserRole
from app.schemas.partner_profile import (
    PartnerProfileCreate,
    PartnerProfileRegistration,
    PartnerProfileRead,
    PartnerProfileUpdate,
)
from app.schemas.user import EntrepreneurRegistration, UserCreate, UserRead
from app.schemas.user_profile import UserProfileRead, UserProfileUpdate
from app.services.partner_service import PartnerService
from app.services.profile_service import ProfileService
from app.services.user_service import UserService

router = APIRouter()


def _parse_partner_json_field(raw_value: Optional[str], field_name: str):
    if not raw_value:
        return None

    try:
        return json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must be valid JSON",
        ) from exc


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    registration_in: EntrepreneurRegistration,
    db: Session = Depends(get_db),
) -> UserRead:
    """Register a regular entrepreneur account using JSON only."""
    user_in = UserCreate(
        email=registration_in.email,
        full_name=registration_in.full_name,
        role=UserRole.ENTREPRENEUR,
        password=registration_in.password,
        confirm_password=registration_in.confirm_password,
    )

    if UserService.get_user_by_email(db, user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    return UserService.create_user(db, user_in)


@router.post(
    "/register-partner",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register Partner Account",
    description=(
        "Register a mentor, supplier, or manufacturer account and upload the "
        "supporting documents during signup."
    ),
    openapi_extra={
        "requestBody": {
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "required": ["email", "role", "password", "confirm_password", "files"],
                        "properties": {
                            "email": {"type": "string", "format": "email"},
                            "full_name": {"type": "string", "nullable": True},
                            "role": {
                                "type": "string",
                                "enum": ["MENTOR", "SUPPLIER", "MANUFACTURER"],
                            },
                            "password": {"type": "string"},
                            "confirm_password": {"type": "string"},
                            "files": {
                                "type": "array",
                                "items": {"type": "string", "format": "binary"},
                                "description": "Upload one or more supporting files",
                            },
                            "company_name": {"type": "string", "nullable": True},
                            "description": {"type": "string", "nullable": True},
                            "services_json": {"type": "string", "nullable": True},
                            "experience_json": {"type": "string", "nullable": True},
                        },
                    },
                    "encoding": {
                        "files": {"contentType": "application/pdf, image/*"},
                    },
                }
            }
        }
    },
)
async def register_partner_user(
    email: str = Form(...),
    full_name: Optional[str] = Form(None),
    role: PartnerType = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    files: List[UploadFile] = File(..., description="Upload one or more supporting files"),
    company_name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    services_json: Optional[str] = Form(None),
    experience_json: Optional[str] = Form(None),
    db: Session = Depends(get_db),
) -> UserRead:
    """Register a partner account using multipart form data."""
    user_in = UserCreate(
        email=email,
        full_name=full_name,
        role=role.value,
        password=password,
        confirm_password=confirm_password,
    )
    partner_profile_in = PartnerProfileRegistration(
        partner_type=role.value,
        company_name=company_name,
        description=description,
        services_json=_parse_partner_json_field(services_json, "services_json"),
        experience_json=_parse_partner_json_field(experience_json, "experience_json"),
    )

    if UserService.get_user_by_email(db, user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    return UserService.create_user(
        db,
        user_in,
        partner_profile_in=partner_profile_in,
        partner_files=files,
    )


@router.post(
    "/profile",
    response_model=UserProfileRead,
    summary="Update User Profile",
    description="Updates the user's profile and refreshes dependent analyses.",
)
async def update_user_profile(
    profile_in: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserProfileRead:
    """Update the authenticated user's profile."""
    updated_profile = ProfileService.update_profile(db, current_user.id, profile_in)
    if not updated_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found",
        )

    return updated_profile


@router.post(
    "/partner-profile",
    response_model=PartnerProfileRead,
    summary="Create Partner Profile",
    description="Submit a request and upload required documents (PDF/Images).",
    openapi_extra={
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
                                "description": "Type of partner role",
                            },
                            "user_id": {"type": "string"},
                            "files": {
                                "type": "array",
                                "items": {"type": "string", "format": "binary"},
                                "description": "Upload PDF or image files",
                            },
                            "company_name": {"type": "string", "nullable": True},
                            "description": {"type": "string", "nullable": True},
                            "services_json": {"type": "string", "nullable": True},
                            "experience_json": {"type": "string", "nullable": True},
                        },
                    },
                    "encoding": {
                        "files": {"contentType": "application/pdf, image/*"},
                    },
                }
            }
        }
    },
)
async def create_partner_profile(
    partner_type: PartnerType = Form(...),
    user_id: str = Form(...),
    files: List[UploadFile] = File(..., description="Upload PDF or image files"),
    company_name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    services_json: Optional[str] = Form(None),
    experience_json: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PartnerProfileRead:
    """Submit a partner profile for the authenticated user."""
    try:
        requested_user_id = UUID(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid user_id") from exc

    if requested_user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="user_id must match the authenticated user",
        )

    profile_in = PartnerProfileCreate(
        partner_type=partner_type,
        company_name=company_name,
        description=description,
        services_json=json.loads(services_json) if services_json else None,
        experience_json=json.loads(experience_json) if experience_json else None,
        user_id=requested_user_id,
    )
    return PartnerService.apply_partner(db, current_user, profile_in, files)


@router.patch(
    "/partner-profile",
    response_model=PartnerProfileRead,
    summary="Update Partner Profile",
)
def update_partner_profile(
    profile_in: PartnerProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PartnerProfileRead:
    """Update the current user's partner profile."""
    return PartnerService.update_profile(db=db, user_id=current_user.id, profile_in=profile_in)


@router.get("/partner-profile", response_model=PartnerProfileRead, summary="Get Partner Profile")
def get_partner_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PartnerProfileRead:
    """Return the current user's partner profile."""
    profile = PartnerService.get_user_profile(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Partner profile not found")

    return profile
