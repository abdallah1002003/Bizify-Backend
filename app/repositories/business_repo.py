from typing import Any

from app.models.business import Business
from app.repositories.base import BaseRepository


class BusinessRepository(BaseRepository[Business, Any, Any]):
    """Data-access helpers for businesses."""


business_repo = BusinessRepository(Business)
