from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.group_invite import GroupInviteStatus
from app.models.group_join_request import GroupJoinRequestStatus
from app.models.group_member import GroupMemberStatus, GroupRole


# ----------------- Group Schemas -----------------
class GroupBase(BaseModel):
    name: str = Field(..., min_length = 3, max_length = 255)
    description: Optional[str] = None
    default_role: GroupRole = GroupRole.VIEWER
    is_chat_enabled: bool = True

class GroupCreate(GroupBase):
    pass

class GroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length = 3, max_length = 255)
    description: Optional[str] = None
    default_role: Optional[GroupRole] = None
    is_chat_enabled: Optional[bool] = None

class GroupResponse(GroupBase):
    id: UUID
    business_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes = True)

# ----------------- Group Member Schemas -----------------
class MemberIdeaInfo(BaseModel):
    id: UUID
    title: str
    
    model_config = ConfigDict(from_attributes = True)

class GroupMemberResponse(BaseModel):
    id: UUID
    user_id: UUID
    group_id: UUID
    email: str
    role: GroupRole
    status: GroupMemberStatus
    accessible_ideas: list[MemberIdeaInfo] = []
    joined_at: datetime
    skill_role: Optional[str] = None

    model_config = ConfigDict(from_attributes = True)

class GroupMemberSkillRoleUpdate(BaseModel):
    skill_role: str = Field(..., min_length=1, max_length=100)

class GroupMemberUpdate(BaseModel):
    role: Optional[GroupRole] = None
    idea_ids: Optional[list[UUID]] = None

    @field_validator("idea_ids", mode = "before")
    @classmethod
    def normalize_idea_ids(cls, v):
        if v in (None, ""):
            return None
        if isinstance(v, list):
            cleaned = [item for item in v if item not in ("", None)]
            return cleaned
        return v

# ----------------- Invite Schemas -----------------
class GroupInviteCreate(BaseModel):
    email: EmailStr
    role: Optional[GroupRole] = None
    idea_ids: Optional[list[UUID]] = Field(
        default = None,
        description = "Optional. Omit this field to invite the user without restricting idea access."
    )

    @field_validator("idea_ids", mode = "before")
    @classmethod
    def normalize_idea_ids(cls, v):
        if v in (None, ""):
            return None
        if isinstance(v, list):
            cleaned = [item for item in v if item not in ("", None)]
            return cleaned
        return v

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "email": "technotop571@gmail.com",
                "role": "VIEWER"
            }
        }
    )

class GroupInviteResponse(BaseModel):
    id: UUID
    group_id: UUID
    email: Optional[str]
    token: str
    role: GroupRole
    status: GroupInviteStatus
    expires_at: datetime
    created_at: datetime
    accessible_ideas: list[MemberIdeaInfo] = []

    model_config = ConfigDict(from_attributes = True)

# ----------------- Join Request Schemas -----------------
class GroupJoinRequestResponse(BaseModel):
    id: UUID
    group_id: UUID
    user_id: UUID
    email: str
    role: GroupRole
    status: GroupJoinRequestStatus
    created_at: datetime
    accessible_ideas: list[MemberIdeaInfo] = []

    model_config = ConfigDict(from_attributes = True)

class HandleJoinRequest(BaseModel):
    is_approved: bool
    role: Optional[GroupRole] = None
    idea_ids: Optional[list[UUID]] = None

    @field_validator("idea_ids", mode = "before")
    @classmethod
    def normalize_idea_ids(cls, v):
        if v in (None, ""):
            return None
        if isinstance(v, list):
            cleaned = [item for item in v if item not in ("", None)]
            return cleaned
        return v
