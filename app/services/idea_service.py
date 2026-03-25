import uuid
from typing import Any, List, Optional

from sqlalchemy.orm import Session

from app.models.group_member import GroupMember, GroupMemberStatus
from app.models.idea import Idea, IdeaStatus
from app.models.group_member import GroupRole

class IdeaService:
    """
    Service class for managing business ideas and collaborations.
    Handles idea lifecycles and provides granular access control for group members.
    """

    @staticmethod
    def get_user_ideas(db: Session, user_id: uuid.UUID) -> List[Idea]:
        """
        Retrieves all ideas where the user is either the owner or an authorized collaborator.
        """
        owned_ideas = db.query(Idea).filter(Idea.owner_id == user_id).all()
        
        shared_ideas = []

        collaborations = db.query(GroupMember).filter(
            GroupMember.user_id == user_id,
            GroupMember.status == GroupMemberStatus.ACTIVE
        ).all()
        
        for collab in collaborations:
            # Add specifically assigned ideas
            if collab.accessible_ideas:
                shared_ideas.extend(collab.accessible_ideas)
            
            # If their role is higher level, they might need access to all business ideas
            if collab.role in [GroupRole.OWNER, GroupRole.EDITOR] and collab.group and collab.group.business_id:
                business_ideas = db.query(Idea).filter(
                    Idea.business_id == collab.group.business_id
                ).all()
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
