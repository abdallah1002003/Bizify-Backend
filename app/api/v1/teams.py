from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_user
from app.services.team_service import TeamService
from app.models.user import User
from uuid import UUID

router = APIRouter()

@router.get("/invites/{token}")
def validate_invitation(token: str, db: Session = Depends(get_db)):
    return TeamService.get_invite_by_token(db, token)

@router.post("/invites/{token}/accept")
def accept_invitation(token: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return TeamService.accept_invitation(db, token, current_user.id)


@router.post("/{business_id}/share")
def create_team_share_link(business_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return TeamService.create_share_link(db, business_id, current_user.id)