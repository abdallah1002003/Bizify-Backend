from typing import Any

from app.models.business import Business
from app.repositories.base import BaseRepository


class BusinessRepository(BaseRepository[Business, Any, Any]):
    """
    Repository for Business database operations.
    """
    pass

business_repo = BusinessRepository(Business)
