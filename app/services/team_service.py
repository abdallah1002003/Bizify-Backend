from sqlalchemy.orm import Session
from uuid import UUID
from app.models.business_invite import BusinessInvite, InviteStatus
from app.models.business_collaborator import BusinessCollaborator, CollaboratorRole # لا تنسى استيراد CollaboratorRole
from fastapi import HTTPException
from datetime import datetime
import secrets 

class TeamService:
    @staticmethod
    def get_invite_by_token(db: Session, token: str):
        invite = db.query(BusinessInvite).filter(BusinessInvite.token == token).first()
        if not invite:
            raise HTTPException(status_code=404, detail="Invitation not found")
        
        if invite.status != InviteStatus.PENDING:
            raise HTTPException(status_code=400, detail=f"Invitation is already {invite.status}")
        
        if invite.expires_at < datetime.utcnow():
            invite.status = InviteStatus.EXPIRED
            db.commit()
            raise HTTPException(status_code=400, detail="Invitation has expired")
            
        return invite

    @staticmethod
    def accept_invitation(db: Session, token: str, user_id: str):
        invite = TeamService.get_invite_by_token(db, token)
        
        existing = db.query(BusinessCollaborator).filter(
            BusinessCollaborator.business_id == invite.business_id,
            BusinessCollaborator.user_id == user_id
        ).first()
        
        if not existing:
            collaborator = BusinessCollaborator(
                business_id=invite.business_id,
                user_id=user_id,
                role=invite.role
            )
            db.add(collaborator)
        
        invite.status = InviteStatus.ACCEPTED
        db.commit()
        return {"message": "Success! You are now part of the team", "business_id": invite.business_id}

    @staticmethod
    def create_share_link(db: Session, business_id: UUID, invited_by: UUID):
        token = secrets.token_urlsafe(32)
        
        from datetime import timedelta
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        invite = BusinessInvite(
            business_id=business_id,
            token=token,
            invited_by=invited_by,
            role=CollaboratorRole.VIEWER,
            expires_at=expires_at,
            email=None
        )
        
        db.add(invite)
        db.commit()
        db.refresh(invite)
        
        return {
            "token": token,
            "invite_url": f"https://bizify.app/join-team?token={token}"
        }
