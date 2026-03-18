from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import EmailStr
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.business import Business
from app.models.business_collaborator import CollaboratorRole
from app.models.business_join_request import BusinessJoinRequest, JoinRequestStatus
from app.models.user import User
from app.schemas.business_join_request import BusinessJoinRequestRead
from app.schemas.business_collaborator import BusinessCollaboratorRead, BusinessMemberRead
from app.services.team_service import TeamService


router = APIRouter()


@router.get("/invites/{token}")
def validate_invitation(token: str, db: Session = Depends(get_db)) -> Any:
    """
    Validates a team invitation token.
    """
    return TeamService.get_invite_by_token(db, token)


@router.post("/invites/accept")
async def accept_invitation(
    token: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Accepts a team invitation (UC_14).
    """
    return await TeamService.accept_invitation(
        db = db,
        token = token,
        user_id = current_user.id,
        background_tasks = background_tasks
    )


@router.get("/join-requests", response_model = List[BusinessJoinRequestRead])
def list_join_requests(
    business_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Lists pending join requests for a business (Owner Only).
    """
    requests = db.query(BusinessJoinRequest).filter(
        BusinessJoinRequest.business_id == business_id,
        BusinessJoinRequest.status == JoinRequestStatus.PENDING
    ).all()
    
    biz = db.query(Business).filter(Business.id == business_id).first()
    
    # Simple owner check
    if not biz or biz.owner_id != current_user.id:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN, 
            detail = "Only owner can view requests"
        )
        
    return requests


@router.post("/join-requests/{request_id}/handle")
async def handle_join_request(
    request_id: UUID,
    is_approved: bool,
    background_tasks: BackgroundTasks,
    role: CollaboratorRole = CollaboratorRole.VIEWER,
    idea_ids: Optional[List[UUID]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Approves or rejects a join request (UC_15).
    """
    return await TeamService.handle_join_request(
        db = db,
        request_id = request_id,
        owner_id = current_user.id,
        is_approved = is_approved,
        background_tasks = background_tasks,
        role = role,
        idea_ids = idea_ids
    )


@router.delete("/{business_id}/members/{user_id}")
async def remove_member(
    business_id: UUID,
    user_id: UUID,
    background_tasks: BackgroundTasks,
    new_owner_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Removes a member from the team (UC_16).
    """
    return await TeamService.remove_collaborator(
        db = db,
        business_id = business_id,
        user_id = user_id,
        owner_id = current_user.id,
        background_tasks = background_tasks,
        new_owner_id = new_owner_id
    )


@router.post("/{business_id}/invites")
def create_invite(
    business_id: UUID,
    email: Optional[EmailStr] = None,
    role: CollaboratorRole = CollaboratorRole.VIEWER,
    is_approval_required: bool = True,
    idea_ids: Optional[List[UUID]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Creates a team invitation link or sends an email (UC_13).
    """
    return TeamService.create_share_link(
        db = db,
        business_id = business_id,
        invited_by = current_user.id,
        email = email,
        role = role,
        is_approval_required = is_approval_required,
        idea_ids = idea_ids
    )


@router.patch("/{business_id}/members/{user_id}/permissions")
async def update_permissions(
    business_id: UUID,
    user_id: UUID,
    background_tasks: BackgroundTasks,
    role: Optional[CollaboratorRole] = None,
    idea_ids: Optional[List[UUID]] = None,
    reassign_to_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Updates member role and resource access (UC_17).
    """
    return await TeamService.update_collaborator(
        db = db,
        business_id = business_id,
        user_id = user_id,
        owner_id = current_user.id,
        background_tasks = background_tasks,
        role = role,
        idea_ids = idea_ids,
        reassign_to_id = reassign_to_id
    )


@router.get("/{business_id}/members", response_model = List[BusinessMemberRead])
def get_team_members(
    business_id: UUID,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[BusinessMemberRead]:
    """
    Retrieves the list of team members for a specific business (UC_19).
    Supports pagination and implements role-based data masking.
    """
    return TeamService.get_collaborators(
        db = db,
        business_id = business_id,
        requester_id = current_user.id,
        skip = skip,
        limit = limit
    )