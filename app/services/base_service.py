<<<<<<< HEAD
# NOTE (Architecture - Afnan):
# BaseService provides dependency injection for the AsyncSession.
# Services inheriting from this class should focus on business logic
# while delegating database access to repositories when possible.

=======
>>>>>>> origin/main
from sqlalchemy.ext.asyncio import AsyncSession

class BaseService:
    """Base class for all services to handle DB session injection."""
    db: AsyncSession

    def __init__(self, db: AsyncSession):
        self.db = db
