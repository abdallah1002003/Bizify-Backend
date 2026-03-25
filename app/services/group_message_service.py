import uuid
from typing import List

from sqlalchemy.orm import Session

from app.models.group_message import GroupMessage
from app.models.group_member import GroupMember

class GroupMessageService:
    @staticmethod
    def create_message(db: Session, group_id: uuid.UUID, sender_id: uuid.UUID, content: str) -> GroupMessage:
        message = GroupMessage(
            group_id=group_id,
            sender_id=sender_id,
            content=content
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def get_group_messages(db: Session, group_id: uuid.UUID, limit: int = 50, offset: int = 0) -> List[GroupMessage]:
        return db.query(GroupMessage).filter(GroupMessage.group_id == group_id).order_by(GroupMessage.created_at.asc()).offset(offset).limit(limit).all()
