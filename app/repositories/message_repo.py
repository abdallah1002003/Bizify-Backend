import uuid
from typing import Any, List

from sqlalchemy.orm import Session

from app.models.group_message import GroupMessage
from app.repositories.base import BaseRepository


class MessageRepository(BaseRepository[GroupMessage, Any, Any]):
    """
    Repository for GroupMessage database operations.
    """

    def get_group_messages(
        self, db: Session, group_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> List[GroupMessage]:
        """
        Fetch messages for a specific group with pagination.
        Ordered chronologically (oldest first).
        """
        return (
            db.query(self.model)
            .filter(self.model.group_id == group_id)
            .order_by(self.model.created_at.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )


message_repo = MessageRepository(GroupMessage)
