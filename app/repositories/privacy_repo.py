import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.privacy_setting import PrivacySetting
from app.repositories.base import BaseRepository


class PrivacyRepository(BaseRepository[PrivacySetting, Any, Any]):
    """
    Repository for PrivacySetting database operations.
    """

    def get_or_create(self, db: Session, user_id: uuid.UUID) -> PrivacySetting:
        """
        Retrieves existing privacy settings or creates defaults.
        """
        privacy = db.query(self.model).filter(self.model.user_id == user_id).first()
        if not privacy:
            privacy = PrivacySetting(user_id=user_id)
            self.save(db, db_obj=privacy)
        return privacy


privacy_repo = PrivacyRepository(PrivacySetting)
