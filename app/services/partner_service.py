from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.partner_profile import PartnerProfile, ApprovalStatus
from app.models.user import User
from app.schemas.partner_profile import PartnerProfileCreate
from uuid import UUID
from datetime import datetime
from typing import Optional

class PartnerService:
    @staticmethod
    def apply_partner(db: Session, user: User, profile_in: PartnerProfileCreate):
        if profile_in.user_id != user.id:
            raise HTTPException(status_code=403, detail="Forbidden")
        
        db_profile = PartnerProfile(
            **profile_in.model_dump(),
            approval_status=ApprovalStatus.PENDING
        )
        db.add(db_profile)
        db.commit()
        db.refresh(db_profile)
        return db_profile

    @staticmethod
    def list_requests(db: Session, status_filter: Optional[ApprovalStatus] = None):
        query = db.query(PartnerProfile)
        if status_filter:
            query = query.filter(PartnerProfile.approval_status == status_filter)
        return query.all()

    @staticmethod
    def approve_request(db: Session, profile_id: UUID, admin_id: UUID):
        profile = db.query(PartnerProfile).filter(PartnerProfile.id == profile_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Request not found")
        
        profile.approval_status = ApprovalStatus.APPROVED
        profile.approved_by = admin_id
        profile.approved_at = datetime.utcnow()
        
        user = db.query(User).filter(User.id == profile.user_id).first()
        if user:
            user.role = profile.partner_type
        
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def reject_request(db: Session, profile_id: UUID, admin_id: UUID):
        profile = db.query(PartnerProfile).filter(PartnerProfile.id == profile_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Request not found")
        
        profile.approval_status = ApprovalStatus.REJECTED
        profile.approved_by = admin_id
        profile.approved_at = datetime.utcnow()
        
        db.commit()
        db.refresh(profile)
        return profile
