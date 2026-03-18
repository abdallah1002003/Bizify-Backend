import os
import shutil
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.models.partner_profile import ApprovalStatus, PartnerProfile
from app.models.user import User
from app.schemas.partner_profile import PartnerProfileCreate


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
            
        profile = PartnerProfile(
            user_id = user.id,
            **profile_in.model_dump(exclude = {"user_id"}),
            documents_json = file_paths
        )
        
        db.add(profile)
        db.commit()
        db.refresh(profile)
        
        return profile

    @staticmethod
    def get_user_profile(
        db: Session,
        user_id: uuid.UUID
    ) -> Optional[PartnerProfile]:
        """
        Retrieves the partner profile for a specific user.
        """
        return db.query(PartnerProfile).filter(PartnerProfile.user_id == user_id).first()

    @staticmethod
    def list_requests(
        db: Session,
        status: Optional[ApprovalStatus] = None
    ) -> List[PartnerProfile]:
        """
        Lists partner profiles, optionally filtering by status.
        """
        query = db.query(PartnerProfile)
        if status:
            query = query.filter(PartnerProfile.approval_status == status)
        return query.all()

    @staticmethod
    def get_all_requests(db: Session) -> List[PartnerProfile]:
        """
        Retrieves all partner applications, regardless of status.
        """
        return PartnerService.list_requests(db)

    @staticmethod
    def get_pending_requests(db: Session) -> List[PartnerProfile]:
        """
        Retrieves all partner applications currently awaiting approval.
        """
        return PartnerService.list_requests(db, status = ApprovalStatus.PENDING)

    @staticmethod
    def get_active_partners(db: Session) -> List[PartnerProfile]:
        """
        Retrieves all currently approved and active partners.
        """
        return db.query(PartnerProfile).filter(
            PartnerProfile.approval_status == ApprovalStatus.APPROVED
        ).all()

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
        """
        profile = db.query(PartnerProfile).filter(PartnerProfile.id == profile_id).first()
        
        if not profile:
            raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND,
                detail = "Request not found"
            )
        
        # Update profile status
        profile.approval_status = ApprovalStatus.APPROVED
        profile.approved_by = admin_id
        profile.approved_at = datetime.now(timezone.utc)
        
        # Upgrade user role
        user = db.query(User).filter(User.id == profile.user_id).first()
        if user:
            user.role = "partner"
            
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
        profile = db.query(PartnerProfile).filter(PartnerProfile.id == profile_id).first()
        
        if not profile:
            raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND,
                detail = "Request not found"
            )
        
        profile.approval_status = ApprovalStatus.REJECTED
        profile.approved_by = admin_id
        profile.approved_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(profile)
        
        return profile
