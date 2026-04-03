import uuid
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.user_profile import GuideStatus, UserProfile
from app.repositories.base import BaseRepository


class ProfileRepository(BaseRepository[UserProfile, Any, Any]):
    """
    Repository for UserProfile-specific database operations.
    """

    def get_by_user_id(self, db: Session, user_id: uuid.UUID) -> Optional[UserProfile]:
        """Fetch the profile for a specific user."""
        return (
            db.query(self.model)
            .filter(self.model.user_id == user_id)
            .first()
        )

    def get_or_create(self, db: Session, user_id: uuid.UUID) -> UserProfile:
        """
        Fetch an existing profile, or create a blank default one if it does not exist.
        Implements lazy initialization to support users who registered before profiles
        were tracked (avoids 404 errors for legacy accounts).
        """
        profile = self.get_by_user_id(db, user_id)
        if not profile:
            profile = UserProfile(
                user_id=user_id,
                guide_status=GuideStatus.NOT_STARTED,
                onboarding_completed=False,
            )
            self.save(db, db_obj=profile)
        return profile


profile_repo = ProfileRepository(UserProfile)
