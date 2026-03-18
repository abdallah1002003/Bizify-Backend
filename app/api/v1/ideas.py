from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.idea import IdeaCreate, IdeaRead
from app.services.idea_service import IdeaService


router = APIRouter()


@router.get("/", response_model = List[IdeaRead])
def get_ideas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[IdeaRead]:
    """
    Retrieves all ideas accessible to the current user, including owned and shared ideas.
    """
    return IdeaService.get_user_ideas(db, current_user.id)


@router.post("/", response_model = IdeaRead)
def create_idea(
    idea_in: IdeaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> IdeaRead:
    """
    Initializes a new business idea. Ensuring the user can only create ideas for themselves.
    """
    if idea_in.owner_id != current_user.id:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN, 
            detail = "You can only create ideas for yourself"
        )
        
    return IdeaService.create_idea(db, current_user.id, idea_in.title, idea_in.description)

