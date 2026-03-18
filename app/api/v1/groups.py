import uuid
from typing import Any, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.team import TeamCreate, TeamRead, TeamUpdate, TeamAccessUpdate, TeamMemberRead
from app.services.group_service import GroupService


router = APIRouter()


@router.post("/businesses/{business_id}/groups", response_model=TeamRead)
def create_group(
    business_id: uuid.UUID,
    group_in: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Creates a new Team/Group inside a business.
    """
    return GroupService.create_team(
        db=db,
        business_id=business_id,
        owner_id=current_user.id,
        team_in=group_in
    )


@router.get("/businesses/{business_id}/groups", response_model=List[TeamRead])
def get_groups(
    business_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Lists all Teams/Groups for a business.
    """
    return GroupService.get_teams(
        db=db,
        business_id=business_id,
        requester_id=current_user.id
    )


@router.put("/{group_id}", response_model=TeamRead)
def update_group(
    group_id: uuid.UUID,
    group_in: TeamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Updates a Team's basic metadata or global role.
    """
    return GroupService.update_team(
        db=db,
        team_id=group_id,
        owner_id=current_user.id,
        team_in=group_in
    )


@router.delete("/{group_id}")
def delete_group(
    group_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Deletes a Team.
    """
    GroupService.delete_team(
        db=db,
        team_id=group_id,
        owner_id=current_user.id
    )
    return {"detail": "Group deleted successfully"}


@router.post("/{group_id}/members/{user_id}", response_model=TeamMemberRead)
def add_group_member(
    group_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Adds a user to a Team.
    """
    return GroupService.add_member(
        db=db,
        team_id=group_id,
        user_id=user_id,
        owner_id=current_user.id
    )


@router.delete("/{group_id}/members/{user_id}")
def remove_group_member(
    group_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Removes a user from a Team.
    """
    GroupService.remove_member(
        db=db,
        team_id=group_id,
        user_id=user_id,
        owner_id=current_user.id
    )
    return {"detail": "Member removed successfully"}


@router.patch("/{group_id}/permissions", response_model=TeamRead)
def update_group_permissions(
    group_id: uuid.UUID,
    access_in: TeamAccessUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Updates the specific ideas a Team has access to.
    """
    return GroupService.update_team_access(
        db=db,
        team_id=group_id,
        owner_id=current_user.id,
        access_in=access_in
    )
