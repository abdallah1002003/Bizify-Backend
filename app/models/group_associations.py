from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base

group_member_idea_access = Table(
    "group_member_idea_access",
    Base.metadata,
    Column("member_id", UUID(as_uuid = True), ForeignKey("group_members.id", ondelete="CASCADE"), primary_key = True),
    Column("idea_id", UUID(as_uuid = True), ForeignKey("ideas.id", ondelete="CASCADE"), primary_key = True)
)

group_invite_idea_access = Table(
    "group_invite_idea_access",
    Base.metadata,
    Column("invite_id", UUID(as_uuid = True), ForeignKey("group_invites.id", ondelete="CASCADE"), primary_key = True),
    Column("idea_id", UUID(as_uuid = True), ForeignKey("ideas.id", ondelete="CASCADE"), primary_key = True)
)

group_request_idea_access = Table(
    "group_request_idea_access",
    Base.metadata,
    Column("request_id", UUID(as_uuid = True), ForeignKey("group_join_requests.id", ondelete="CASCADE"), primary_key = True),
    Column("idea_id", UUID(as_uuid = True), ForeignKey("ideas.id", ondelete="CASCADE"), primary_key = True)
)
