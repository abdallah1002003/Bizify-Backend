import uuid
from typing import Any, List, Optional

from sqlalchemy.orm import Session

from app.models.business_collaborator import BusinessCollaborator
from app.models.idea import Idea, IdeaStatus
from app.models.team_member import TeamMember




class IdeaService:
    """
    Service class for managing business ideas and collaborations.
    Handles idea lifecycles and provides granular access control for team members.
    """

    @staticmethod
    def get_user_ideas(db: Session, user_id: uuid.UUID) -> List[Idea]:
        """
        Retrieves all ideas where the user is either the owner or an authorized collaborator.
        """
        owned_ideas = db.query(Idea).filter(Idea.owner_id == user_id).all()
        
        collaborations = db.query(BusinessCollaborator).filter(
            BusinessCollaborator.user_id == user_id
        ).all()
        
        shared_ideas = []
        
        for collab in collaborations:
            if collab.accessible_ideas:
                shared_ideas.extend(collab.accessible_ideas)
            elif collab.idea_id:
                legacy_idea = db.query(Idea).filter(Idea.id == collab.idea_id).first()
                
                if legacy_idea:
                    shared_ideas.append(legacy_idea)
            else:
                business_ideas = db.query(Idea).filter(Idea.business_id == collab.business_id).all()
                shared_ideas.extend(business_ideas)
                
        team_memberships = db.query(TeamMember).filter(TeamMember.user_id == user_id).all()
        for membership in team_memberships:
            if membership.team.accessible_ideas:
                shared_ideas.extend(membership.team.accessible_ideas)
            else:
                business_ideas = db.query(Idea).filter(Idea.business_id == membership.team.business_id).all()
                shared_ideas.extend(business_ideas)
                
        unique_ideas = list({idea.id: idea for idea in (owned_ideas + shared_ideas)}.values())
        
        return unique_ideas

    @staticmethod
    def create_idea(
        db: Session, 
        user_id: uuid.UUID, 
        title: str, 
        description: Optional[str] = None
    ) -> Idea:
        """
        Initializes a new business idea in DRAFT status for a specific user.
        """
        idea = Idea(
            owner_id = user_id,
            title = title,
            description = description,
            status = IdeaStatus.DRAFT
        )
        
        db.add(idea)
        
        db.commit()
        db.refresh(idea)
        
        return idea
