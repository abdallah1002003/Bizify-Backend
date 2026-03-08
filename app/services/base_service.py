from sqlalchemy.ext.asyncio import AsyncSession

class BaseService:
    """Base class for all services to handle DB session injection."""
    db: AsyncSession

    def __init__(self, db: AsyncSession):
        self.db = db
