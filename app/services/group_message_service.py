import uuid
from typing import List

from sqlalchemy.orm import Session

from app.models.group_message import GroupMessage
from app.repositories.message_repo import message_repo


class GroupMessageService:
    @staticmethod
    def create_message(db: Session, group_id: uuid.UUID, sender_id: uuid.UUID, content: str) -> GroupMessage:
        return message_repo.create(db, obj_in={
            "group_id": group_id,
            "sender_id": sender_id,
            "content": content
        })

    @staticmethod
    def get_group_messages(db: Session, group_id: uuid.UUID, limit: int = 50, offset: int = 0) -> List[GroupMessage]:
        return message_repo.get_group_messages(db, group_id, limit, offset)
