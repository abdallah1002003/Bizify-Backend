from sqlalchemy.orm import Session

class BaseService:
    """Base class for all services to handle DB session injection."""
    def __init__(self, db: Session):
        self.db = db
