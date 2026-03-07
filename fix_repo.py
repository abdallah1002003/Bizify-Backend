import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.repositories.base_repository import GenericRepository
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()

class MockTestModel(Base):
    __tablename__ = "mock_test_model"
    id = Column(Integer, primary_key=True)
    name = Column(String)

@pytest.mark.asyncio
async def test_gen_repo():
    db = AsyncMock()
    repo = GenericRepository(db, MockTestModel)
    
    mock_sc = MagicMock()
    mock_sc.scalars().all.return_value = [MockTestModel(id=1), MockTestModel(id=2)]
    db.execute.return_value = mock_sc
    res_all = await repo.get_all(skip=0, limit=10)
    assert len(res_all) == 2

    # update with dict
    obj = MockTestModel(id=1, name="old")
    await repo.update(obj, {"name": "new"})
    assert obj.name == "new"

    return True
