import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.group_member import GroupRole
from app.models.idea import Idea, IdeaStatus
from app.repositories.idea_repo import idea_repo
from app.repositories.group_repo import group_repo


class IdeaService:
    """
    Service class for managing business ideas and collaborations.
    All DB queries are delegated to idea_repo and group_repo.
    Business logic: access control, role-based idea visibility, deduplication.
    """

    @staticmethod
    def get_user_ideas(db: Session, user_id: uuid.UUID) -> List[Idea]:
        """
        Returns all ideas accessible to the user:
        - Ideas they own directly.
        - Ideas shared with them via group membership (role-based access).
        """
        owned_ideas = idea_repo.get_by_owner(db, user_id)

        shared_ideas = []

        # Fetch all active group memberships for this user via group_repo
        collaborations = group_repo.get_active_members_for_user(db, user_id)

        for collab in collaborations:
            # Add specifically assigned ideas
            if collab.accessible_ideas:
                shared_ideas.extend(collab.accessible_ideas)

            # OWNER and EDITOR roles get access to all ideas in the business
            if (
                collab.role in [GroupRole.OWNER, GroupRole.EDITOR]
                and collab.group
                and collab.group.business_id
            ):
                business_ideas = idea_repo.get_by_business(db, collab.group.business_id)
                shared_ideas.extend(business_ideas)

        # Deduplicate by idea ID
        unique_ideas = list({idea.id: idea for idea in (owned_ideas + shared_ideas)}.values())
        return unique_ideas

    @staticmethod
    def create_idea(
        db: Session,
        user_id: uuid.UUID,
        title: str,
        description: Optional[str] = None,
    ) -> Idea:
        """
        Initializes a new business idea in DRAFT status for a specific user.
        """
        return idea_repo.create(db, obj_in={
            "owner_id": user_id,
            "title": title,
            "description": description,
            "status": IdeaStatus.DRAFT,
        })
