from sqlalchemy import Column, Integer, String
from app.db.database import Base

class MockTestModel(Base):
    __tablename__ = "mock_test_model"
    id = Column(Integer, primary_key=True)
    name = Column(String)
