from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.notification import NotificationStatus, DeliveryStatus


# --- Notification Settings Schemas ---

class NotificationSettingBase(BaseModel):
    is_enabled: bool = True
    email_enabled: bool = True
    sms_enabled: bool = False
    push_enabled: bool = True
    marketing_enabled: bool = False
    team_updates_enabled: bool = True
    billing_alerts_enabled: bool = True


class NotificationSettingRead(NotificationSettingBase):
    user_id: UUID
    
    model_config = ConfigDict(from_attributes = True)


class NotificationSettingUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    marketing_enabled: Optional[bool] = None
    team_updates_enabled: Optional[bool] = None
    billing_alerts_enabled: Optional[bool] = None


# --- Notification Schemas ---

class NotificationBase(BaseModel):
    title: str
    content: str
    type: str
    expires_at: Optional[datetime] = None


class NotificationCreate(NotificationBase):
    user_id: UUID


class NotificationRead(NotificationBase):
    id: UUID
    user_id: UUID
    status: NotificationStatus
    delivery_status: DeliveryStatus
    created_at: datetime
    
    model_config = ConfigDict(from_attributes = True)


class NotificationUpdateStatus(BaseModel):
    status: NotificationStatus = Field(..., description = "Target status (READ or DISMISSED)")


class NotificationBulkUpdateStatus(BaseModel):
    notification_ids: List[UUID]
    status: NotificationStatus = Field(..., description = "Target status for all selected notifications")


class NotificationList(BaseModel):
    total: int
    items: List[NotificationRead]
