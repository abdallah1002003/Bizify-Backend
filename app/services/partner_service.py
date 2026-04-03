import os
import shutil
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.models.partner_profile import ApprovalStatus, PartnerProfile
from app.models.user import User, UserRole
from app.schemas.partner_profile import PartnerProfileCreate
from app.repositories.partner_repo import partner_repo
from app.repositories.user_repo import user_repo


class PartnerService:
    """
    Service class for managing partner applications and profiles.
    Includes logic for processing requests, handling file uploads,
    and managing administrative approval status.
    """
    
    @staticmethod
    def apply_partner(
        db: Session,
        user: User,
        profile_in: PartnerProfileCreate,
        files: List[UploadFile]
    ) -> PartnerProfile:
        """
        Handles the full partner application process, including document storage.
        """
        file_paths = []
        for file in files:
            path = PartnerService.save_id_document(user.id, file)
            file_paths.append(path)
            
        profile = partner_repo.create(db, obj_in={
            "user_id": user.id,
            **profile_in.model_dump(exclude={"user_id"}),
            "documents_json": file_paths
        })
        
        return profile

    @staticmethod
    def get_user_profile(
        db: Session,
        user_id: uuid.UUID
    ) -> Optional[PartnerProfile]:
        """Retrieves the partner profile for a specific user."""
        return partner_repo.get_by_user_id(db, user_id)

    @staticmethod
    def list_requests(
        db: Session,
        status: Optional[ApprovalStatus] = None
    ) -> List[PartnerProfile]:
        """List partner profiles, optionally filtering by approval status."""
        return partner_repo.get_filtered(db, status)

    @staticmethod
    def get_all_requests(db: Session) -> List[PartnerProfile]:
        """Return all partner applications regardless of status."""
        return partner_repo.get_all(db)

    @staticmethod
    def get_pending_requests(db: Session) -> List[PartnerProfile]:
        """Return all pending partner applications."""
        return partner_repo.get_pending(db)

    @staticmethod
    def get_active_partners(db: Session) -> List[PartnerProfile]:
        """Return all approved and active partners."""
        return partner_repo.get_approved(db)

    @staticmethod
    def save_id_document(
        user_id: uuid.UUID,
        file: UploadFile
    ) -> str:
        """
        Saves a partner's identification document to the secure storage.
        """
        upload_dir = os.path.join("uploads", "partners", str(user_id))
        os.makedirs(upload_dir, exist_ok = True)
        
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return file_path

    @staticmethod
    def approve_request(
        db: Session,
        profile_id: uuid.UUID,
        admin_id: uuid.UUID
    ) -> PartnerProfile:
        """
        Approves a partner application and upgrades the user's role.
        Business logic: validate existence, update approval fields, upgrade role.
        """
        profile = partner_repo.get_by_profile_id(db, profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found",
            )
        profile.approval_status = ApprovalStatus.APPROVED
        profile.approved_by = admin_id
        profile.approved_at = datetime.now(timezone.utc)

        # Upgrade user role via user_repo
        user = user_repo.get(db, profile.user_id)
        if user:
            user.role = UserRole(profile.partner_type.value)
            user_repo.save(db, db_obj=user, commit=False, refresh=False)

        partner_repo.save(db, db_obj=profile, commit=False, refresh=False)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def reject_request(
        db: Session,
        profile_id: uuid.UUID,
        admin_id: uuid.UUID
    ) -> PartnerProfile:
        """
        Rejects a partner application without changing the user's base role.
        """
        profile = partner_repo.get_by_profile_id(db, profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found",
            )
        profile.approval_status = ApprovalStatus.REJECTED
        profile.approved_by = admin_id
        profile.approved_at = datetime.now(timezone.utc)
        partner_repo.save(db, db_obj=profile)
        db.refresh(profile)
        return profile
