import uuid
from typing import Any, List, Optional

from sqlalchemy.orm import Session

from app.models.business import Business
from app.models.group import Group
from app.models.group_invite import GroupInvite, GroupInviteStatus
from app.models.group_join_request import GroupJoinRequest, GroupJoinRequestStatus
from app.models.group_member import GroupMember, GroupMemberStatus
from app.repositories.base import BaseRepository


class GroupRepository(BaseRepository[Group, Any, Any]):
    """Data-access helpers for groups and related membership records."""

    def get_by_id(self, db: Session, group_id: uuid.UUID) -> Optional[Group]:
        """Fetch a single group by its primary key."""
        return db.query(self.model).filter(self.model.id == group_id).first()

    def get_by_business_id(self, db: Session, business_id: uuid.UUID) -> List[Group]:
        """Fetch all groups belonging to a specific business."""
        return db.query(self.model).filter(self.model.business_id == business_id).all()

    def get_user_owned_groups(self, db: Session, user_id: uuid.UUID) -> List[Group]:
        """Fetch all groups owned by a user through business ownership."""
        return db.query(Group).join(Business).filter(Business.owner_id == user_id).all()

    def get_user_member_groups(self, db: Session, user_id: uuid.UUID) -> List[Group]:
        """Fetch all groups where the user is an active member."""
        return (
            db.query(Group)
            .join(GroupMember)
            .filter(
                GroupMember.user_id == user_id,
                GroupMember.status == GroupMemberStatus.ACTIVE,
            )
            .all()
        )

    def get_active_members(self, db: Session, group_id: uuid.UUID) -> List[GroupMember]:
        """Fetch all active members of a group."""
        return (
            db.query(GroupMember)
            .filter(
                GroupMember.group_id == group_id,
                GroupMember.status == GroupMemberStatus.ACTIVE,
            )
            .all()
        )

    def get_active_members_for_user(self, db: Session, user_id: uuid.UUID) -> List[GroupMember]:
        """Fetch all active memberships for a user across groups."""
        return (
            db.query(GroupMember)
            .filter(
                GroupMember.user_id == user_id,
                GroupMember.status == GroupMemberStatus.ACTIVE,
            )
            .all()
        )

    def get_member_by_user_and_group(
        self,
        db: Session,
        group_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[GroupMember]:
        """Fetch a membership by group and user identifiers."""
        return (
            db.query(GroupMember)
            .filter(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
            .first()
        )

    def is_active_member(self, db: Session, group_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Return whether the user is an active member of a group."""
        return (
            db.query(GroupMember)
            .filter(
                GroupMember.group_id == group_id,
                GroupMember.user_id == user_id,
                GroupMember.status == GroupMemberStatus.ACTIVE,
            )
            .first()
            is not None
        )

    def get_member_by_id(self, db: Session, member_id: uuid.UUID) -> Optional[GroupMember]:
        """Fetch a group member record by its ID."""
        return db.query(GroupMember).filter(GroupMember.id == member_id).first()

    def is_member_of_business(
        self,
        db: Session,
        business_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[GroupMember]:
        """Return a matching active membership within a business, if any."""
        return (
            db.query(GroupMember)
            .join(Group)
            .filter(
                Group.business_id == business_id,
                GroupMember.user_id == user_id,
                GroupMember.status == GroupMemberStatus.ACTIVE,
            )
            .first()
        )

    def get_pending_invite_by_token(self, db: Session, token: str) -> Optional[GroupInvite]:
        """Fetch a pending invite using its secret token."""
        return (
            db.query(GroupInvite)
            .filter(
                GroupInvite.token == token,
                GroupInvite.status == GroupInviteStatus.PENDING,
            )
            .first()
        )

    def get_pending_join_request(
        self,
        db: Session,
        request_id: uuid.UUID,
    ) -> Optional[GroupJoinRequest]:
        """Fetch a pending join request by its ID."""
        return (
            db.query(GroupJoinRequest)
            .filter(
                GroupJoinRequest.id == request_id,
                GroupJoinRequest.status == GroupJoinRequestStatus.PENDING,
            )
            .first()
        )

    def create_member(self, db: Session, member: GroupMember, *, commit: bool = True) -> GroupMember:
        """Create and save a new group member."""
        db.add(member)
        if commit:
            db.commit()
        else:
            db.flush()
        db.refresh(member)
        return member

    def save_member(self, db: Session, member: GroupMember, *, commit: bool = True) -> GroupMember:
        """Persist updates to an existing group member."""
        db.add(member)
        if commit:
            db.commit()
        else:
            db.flush()
        db.refresh(member)
        return member

    def create_invite(self, db: Session, invite: GroupInvite, *, commit: bool = True) -> GroupInvite:
        """Create and save a new group invite."""
        db.add(invite)
        if commit:
            db.commit()
        else:
            db.flush()
        db.refresh(invite)
        return invite

    def save_invite(self, db: Session, invite: GroupInvite, *, commit: bool = True) -> GroupInvite:
        """Persist updates to an existing invite."""
        db.add(invite)
        if commit:
            db.commit()
        else:
            db.flush()
        db.refresh(invite)
        return invite

    def create_join_request(
        self,
        db: Session,
        request: GroupJoinRequest,
        *,
        commit: bool = True,
    ) -> GroupJoinRequest:
        """Create and save a new join request."""
        db.add(request)
        if commit:
            db.commit()
        else:
            db.flush()
        db.refresh(request)
        return request

    def save_join_request(
        self,
        db: Session,
        request: GroupJoinRequest,
        *,
        commit: bool = True,
    ) -> GroupJoinRequest:
        """Persist updates to an existing join request."""
        db.add(request)
        if commit:
            db.commit()
        else:
            db.flush()
        db.refresh(request)
        return request

    def remove_member(self, db: Session, member: GroupMember, *, commit: bool = True) -> None:
        """Delete a group member record."""
        db.delete(member)
        if commit:
            db.commit()
        else:
            db.flush()


group_repo = GroupRepository(Group)
