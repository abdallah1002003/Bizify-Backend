from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.idea import IdeaCreate, IdeaRead
from app.services.idea_service import IdeaService

router = APIRouter()


@router.get("/", response_model=List[IdeaRead])
def get_ideas(
    min_budget: Optional[float] = Query(None, description="Minimum allowed budget"),
    max_budget: Optional[float] = Query(None, description="Maximum allowed budget"),
    skills: Optional[str] = Query(None, description="Comma-separated skills (e.g., Python,React)"),
    feasibility: Optional[float] = Query(None, description="Minimum feasibility score required"),
    sort_by: str = Query("created_at", description="Field to sort by (e.g., budget, feasibility, ai_score)"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[IdeaRead]:
    """Return the current user's accessible ideas with filters and sorting."""
    if min_budget is not None and max_budget is not None and min_budget > max_budget:
        raise HTTPException(
            status_code=400,
            detail="Invalid data: Minimum budget cannot be greater than maximum budget.",
        )

    skills_list = [skill.strip() for skill in skills.split(",")] if skills else None
    return IdeaService.get_user_ideas(
        db=db,
        user_id=current_user.id,
        min_budget=min_budget,
        max_budget=max_budget,
        skills=skills_list,
        feasibility=feasibility,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.post("/", response_model=IdeaRead)
def create_idea(
    idea_in: IdeaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IdeaRead:
    """Create a new business idea for the authenticated user."""
    return IdeaService.create_idea(db, current_user.id, idea_in.title, idea_in.description)


@router.get("/archived", response_model=List[IdeaRead])
def get_archived_ideas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[IdeaRead]:
    """Return archived ideas accessible to the current user."""
    return IdeaService.get_archived_user_ideas(db=db, user_id=current_user.id)


@router.patch("/{idea_id}/archive", response_model=IdeaRead)
def archive_idea(
    idea_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IdeaRead:
    """Archive a business idea."""
    return IdeaService.archive_idea(db=db, idea_id=idea_id, user_id=current_user.id)


@router.patch("/{idea_id}/unarchive", response_model=IdeaRead)
def unarchive_idea(
    idea_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IdeaRead:
    """Restore an archived business idea."""
    return IdeaService.unarchive_idea(db=db, idea_id=idea_id, user_id=current_user.id)
