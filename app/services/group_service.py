import logging
import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.business import Business
from app.models.business_collaborator import BusinessCollaborator, CollaboratorRole
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.team_idea_access import TeamIdeaAccess
from app.schemas.team import TeamCreate, TeamUpdate, TeamAccessUpdate


logger = logging.getLogger(__name__)


class GroupService:
    """
    Service for managing custom Teams (Groups) within a Business.
    """

    @staticmethod
    def _check_owner(db: Session, business_id: uuid.UUID, user_id: uuid.UUID) -> Business:
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")
        
        # Check if user is owner of the business (or maybe just an owner-level collaborator)
        if business.owner_id != user_id:
            # Check collab
            collab = db.query(BusinessCollaborator).filter(
                BusinessCollaborator.business_id == business_id,
                BusinessCollaborator.user_id == user_id,
                BusinessCollaborator.role == CollaboratorRole.OWNER
            ).first()
            if not collab:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owners can manage teams")
        return business

    @staticmethod
    def create_team(db: Session, business_id: uuid.UUID, owner_id: uuid.UUID, team_in: TeamCreate) -> Team:
        GroupService._check_owner(db, business_id, owner_id)
        
        team = Team(
            business_id=business_id,
            name=team_in.name,
            description=team_in.description,
            role=team_in.role
        )
        db.add(team)
        db.flush()
        
        # Add idea access if any
        if team_in.idea_ids:
            for i_id in team_in.idea_ids:
                access = TeamIdeaAccess(team_id=team.id, idea_id=i_id)
                db.add(access)
                
        db.commit()
        db.refresh(team)
        return team

    @staticmethod
    def get_teams(db: Session, business_id: uuid.UUID, requester_id: uuid.UUID) -> List[Team]:
        # Anyone in the business should be able to see the teams probably
        return db.query(Team).filter(Team.business_id == business_id).all()

    @staticmethod
    def update_team(db: Session, team_id: uuid.UUID, owner_id: uuid.UUID, team_in: TeamUpdate) -> Team:
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
            
        GroupService._check_owner(db, team.business_id, owner_id)
        
        if team_in.name is not None:
            team.name = team_in.name
        if team_in.description is not None:
            team.description = team_in.description
        if team_in.role is not None:
            team.role = team_in.role
            
        db.commit()
        db.refresh(team)
        return team

    @staticmethod
    def delete_team(db: Session, team_id: uuid.UUID, owner_id: uuid.UUID) -> None:
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
            
        GroupService._check_owner(db, team.business_id, owner_id)
        db.delete(team)
        db.commit()

    @staticmethod
    def add_member(db: Session, team_id: uuid.UUID, user_id: uuid.UUID, owner_id: uuid.UUID) -> TeamMember:
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
            
        GroupService._check_owner(db, team.business_id, owner_id)
        
        # Check if user is part of the business
        if team.business.owner_id != user_id:
            collab = db.query(BusinessCollaborator).filter(
                BusinessCollaborator.business_id == team.business_id,
                BusinessCollaborator.user_id == user_id
            ).first()
            if not collab:
                raise HTTPException(status_code=400, detail="User is not a collaborator in this business")
                
        # Check if already in team
        existing = db.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="User is already in this team")
            
        member = TeamMember(team_id=team_id, user_id=user_id)
        db.add(member)
        db.commit()
        db.refresh(member)
        return member

    @staticmethod
    def remove_member(db: Session, team_id: uuid.UUID, user_id: uuid.UUID, owner_id: uuid.UUID) -> None:
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
            
        GroupService._check_owner(db, team.business_id, owner_id)
        
        member = db.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id).first()
        if not member:
            raise HTTPException(status_code=404, detail="User is not in this team")
            
        db.delete(member)
        db.commit()

    @staticmethod
    def update_team_access(db: Session, team_id: uuid.UUID, owner_id: uuid.UUID, access_in: TeamAccessUpdate) -> Team:
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
            
        GroupService._check_owner(db, team.business_id, owner_id)
        
        # Clear existing
        db.query(TeamIdeaAccess).filter(TeamIdeaAccess.team_id == team_id).delete()
        
        # Set new
        for i_id in access_in.idea_ids:
            access = TeamIdeaAccess(team_id=team_id, idea_id=i_id)
            db.add(access)
            
        db.commit()
        db.refresh(team)
        return team
