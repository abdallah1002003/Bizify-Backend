import uuid
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.ai.idea import Idea, IdeaStatus
from app.models.group_member import GroupRole
from app.repositories.group_repo import group_repo
from app.repositories.idea_repo import idea_repo


class IdeaService:
    """Idea workflows with access control and filtering rules."""

    @staticmethod
    def _get_accessible_ideas(db: Session, user_id: uuid.UUID) -> list[Idea]:
        """Collect ideas the user owns or can access through groups."""
        owned_ideas = idea_repo.get_by_owner(db, user_id)
        shared_ideas: list[Idea] = []
        collaborations = group_repo.get_active_members_for_user(db, user_id)

        for collaboration in collaborations:
            if collaboration.accessible_ideas:
                shared_ideas.extend(collaboration.accessible_ideas)

            if (
                collaboration.role in [GroupRole.OWNER, GroupRole.EDITOR]
                and collaboration.group
                and collaboration.group.business_id
            ):
                shared_ideas.extend(
                    idea_repo.get_by_business(db, collaboration.group.business_id)
                )

        return list({idea.id: idea for idea in owned_ideas + shared_ideas}.values())

    @staticmethod
    def get_user_ideas(
        db: Session,
        user_id: uuid.UUID,
        min_budget: Optional[float] = None,
        max_budget: Optional[float] = None,
        skills: Optional[list[str]] = None,
        feasibility: Optional[float] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> list[Idea]:
        """Return accessible ideas after applying filters and sorting."""
        filtered_items: list[tuple[Idea, int]] = []

        for idea in IdeaService._get_accessible_ideas(db, user_id):
            if idea.is_archived:
                continue

            if min_budget is not None and idea.budget is not None and idea.budget < min_budget:
                continue

            if max_budget is not None and idea.budget is not None and idea.budget > max_budget:
                continue

            if (
                feasibility is not None
                and idea.feasibility is not None
                and idea.feasibility < feasibility
            ):
                continue

            match_count = 0
            if skills:
                idea_skills = set(idea.skills or [])
                requested_skills = set(skills)
                match_count = len(requested_skills.intersection(idea_skills))
                if match_count == 0:
                    continue

            filtered_items.append((idea, match_count))

        def sort_key(item: tuple[Idea, int]) -> tuple[int, object]:
            idea, match_count = item
            field_value = getattr(idea, sort_by, idea.created_at)
            if field_value is None:
                field_value = 0
            return match_count, field_value

        filtered_items.sort(
            key=sort_key,
            reverse=sort_order.lower() == "desc",
        )
        return [idea for idea, _ in filtered_items]

    @staticmethod
    def get_archived_user_ideas(db: Session, user_id: uuid.UUID) -> list[Idea]:
        """Return only archived ideas accessible to the user."""
        return [
            idea
            for idea in IdeaService._get_accessible_ideas(db, user_id)
            if idea.is_archived
        ]

    @staticmethod
    def get_idea(db: Session, idea_id: uuid.UUID, user_id: uuid.UUID) -> Idea:
        """Return a single idea the user can access."""
        idea = idea_repo.get(db, id=idea_id)
        if not idea:
            raise HTTPException(status_code=404, detail="Idea not found")
        accessible_ids = {i.id for i in IdeaService._get_accessible_ideas(db, user_id)}
        if idea_id not in accessible_ids:
            raise HTTPException(status_code=403, detail="Not authorized to access this idea")
        return idea

    @staticmethod
    def update_idea(
        db: Session,
        idea_id: uuid.UUID,
        user_id: uuid.UUID,
        updates: dict,
    ) -> Idea:
        """Update an idea the user owns."""
        idea = idea_repo.get(db, id=idea_id)
        if not idea:
            raise HTTPException(status_code=404, detail="Idea not found")
        if idea.owner_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to modify this idea")
        return idea_repo.update(db, db_obj=idea, obj_in=updates)

    @staticmethod
    def delete_idea(db: Session, idea_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Delete an idea the user owns."""
        idea = idea_repo.get(db, id=idea_id)
        if not idea:
            raise HTTPException(status_code=404, detail="Idea not found")
        if idea.owner_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this idea")
        idea_repo.remove(db, id=idea_id)

    @staticmethod
    def create_idea(
        db: Session,
        user_id: uuid.UUID,
        title: str,
        description: Optional[str] = None,
    ) -> Idea:
        """Create a new draft idea for a user."""
        return idea_repo.create(
            db,
            obj_in={
                "owner_id": user_id,
                "title": title,
                "description": description,
                "status": IdeaStatus.DRAFT,
            },
        )

    @staticmethod
    def archive_idea(db: Session, idea_id: uuid.UUID, user_id: uuid.UUID) -> Idea:
        """Archive an idea owned by the user."""
        idea = idea_repo.get(db, id=idea_id)
        if not idea:
            raise HTTPException(status_code=404, detail="Idea not found")

        if idea.owner_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to archive this idea")

        if idea.is_archived:
            return idea

        try:
            return idea_repo.update(
                db,
                db_obj=idea,
                obj_in={"is_archived": True, "archived_at": datetime.utcnow()},
            )
        except Exception as exc:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="An error occurred while archiving the idea. Please try again later.",
            ) from exc

    @staticmethod
    def unarchive_idea(db: Session, idea_id: uuid.UUID, user_id: uuid.UUID) -> Idea:
        """Restore an archived idea owned by the user."""
        idea = idea_repo.get(db, id=idea_id)
        if not idea:
            raise HTTPException(status_code=404, detail="Idea not found")

        if idea.owner_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to unarchive this idea",
            )

        if not idea.is_archived:
            return idea

        try:
            return idea_repo.update(
                db,
                db_obj=idea,
                obj_in={"is_archived": False, "archived_at": None},
            )
        except Exception as exc:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="An error occurred while unarchiving the idea. Please try again later.",
            ) from exc
