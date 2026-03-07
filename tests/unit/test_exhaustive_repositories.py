"""Exhaustive tests for the Repository layer resolving coverage gaps."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String
from app.repositories.base_repository import GenericRepository
from app.repositories.auth_repository import RefreshTokenRepository, EmailVerificationTokenRepository, PasswordResetTokenRepository

# ── GenericRepository ──────────────────────────────────────────────────────────

Base = declarative_base()

class MockModel(Base):
    __tablename__ = "mock_model"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    a = Column(String)
    c = Column(String)
    e = Column(String)
            
    def model_dump(self, exclude_unset=False):
        return {"a": "b"}

class MockModelDict:
    def dict(self, exclude_unset=False):
        return {"c": "d"}


@pytest.mark.asyncio
async def test_generic_repository_exhaustive():
    db = AsyncMock()
    repo = GenericRepository(db, MockModel)
    
    # get
    db.get.return_value = MockModel(id=1)
    res = await repo.get(1)
    assert res.id == 1
    
    # get_all
    mock_sc = MagicMock()
    mock_sc.scalars().all.return_value = [MockModel(id=1), MockModel(id=2)]
    db.execute.return_value = mock_sc
    res_all = await repo.get_all(skip=0, limit=10)
    assert len(res_all) == 2
    
    # count
    mock_count = MagicMock()
    mock_count.scalar.return_value = 5
    db.execute.return_value = mock_count
    assert await repo.count() == 5
    
    # create
    await repo.create({"id": 1})
    db.commit.assert_called()
    db.refresh.assert_called()
    
    db.commit.reset_mock()
    await repo.create({"id": 2}, auto_commit=False)
    db.flush.assert_called()
    db.commit.assert_not_called()
    
    # update with dict
    obj = MockModel(id=1, name="old")
    await repo.update(obj, {"name": "new"})
    assert obj.name == "new"
    
    # update with model_dump
    obj2 = MockModel(id=2, a="old")
    await repo.update(obj2, MockModel())
    assert obj2.a == "b"
    
    # update with dict method
    obj3 = MockModel(id=3, c="old")
    await repo.update(obj3, MockModelDict(), auto_commit=False)
    assert obj3.c == "d"
    
    # update with object (dict(obj))
    obj4 = MockModel(id=4, e="old")
    await repo.update(obj4, [("e", "f")])
    assert obj4.e == "f"
    
    # delete by ID
    db.get.return_value = obj
    await repo.delete(1)
    db.delete.assert_called_with(obj)
    
    # delete by instance
    await repo.delete(obj, auto_commit=False)
    # delete missing
    db.get.return_value = None
    assert await repo.delete(999) is None
    
    # proxy methods
    await repo.commit()
    await repo.rollback()
    await repo.flush()
    await repo.refresh(obj)


# ── Auth Repositories ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_auth_repositories_exhaustive():
    db = AsyncMock()
    
    # RefreshTokenRepository
    r_repo = RefreshTokenRepository(db)
    
    mock_sc = MagicMock()
    mock_sc.scalar_one_or_none.return_value = MagicMock(jti="j1")
    db.execute.return_value = mock_sc
    
    assert (await r_repo.get_by_jti("j1")).jti == "j1"
    
    with patch.object(r_repo, "create", new_callable=AsyncMock) as m_create:
        m_create.return_value = MagicMock()
        assert await r_repo.create_safe({"jti": "j1"}) is not None
        
        m_create.side_effect = IntegrityError("a", "b", "c")
        assert await r_repo.create_safe({"jti": "j2"}) is None
        db.rollback.assert_called()
        
    with patch.object(r_repo, "get_by_jti", return_value=MagicMock()) as _m_get_jti, \
         patch.object(r_repo, "update", new_callable=AsyncMock) as m_upd:
         
         await r_repo.revoke("j1")
         m_upd.assert_called()
         
    mock_cursor = MagicMock()
    mock_cursor.rowcount = 5
    db.execute.return_value = mock_cursor
    assert await r_repo.delete_expired() == 5
    
    # EmailVerificationTokenRepository
    e_repo = EmailVerificationTokenRepository(db)
    mock_sc.scalar_one_or_none.return_value = MagicMock(jti="e1")
    db.execute.return_value = mock_sc
    
    assert (await e_repo.get_by_jti("e1")).jti == "e1"
    
    with patch.object(e_repo, "create", new_callable=AsyncMock) as m_create:
        m_create.return_value = MagicMock()
        assert await e_repo.create_safe({"jti": "e1"}) is not None
        
        m_create.side_effect = IntegrityError("a", "b", "c")
        assert await e_repo.create_safe({"jti": "e2"}) is None
        
    mock_tok = MagicMock(used=False)
    await e_repo.mark_used(mock_tok)
    assert mock_tok.used is True
    await e_repo.mark_used(mock_tok, auto_commit=False)
    
    db.execute.return_value = mock_cursor
    assert await e_repo.delete_expired_or_used() == 5
    
    # PasswordResetTokenRepository
    p_repo = PasswordResetTokenRepository(db)
    mock_sc.scalar_one_or_none.return_value = MagicMock(jti="p1")
    db.execute.return_value = mock_sc
    
    assert (await p_repo.get_by_jti("p1")).jti == "p1"
    
    with patch.object(p_repo, "create", new_callable=AsyncMock) as m_create:
        m_create.return_value = MagicMock()
        assert await p_repo.create_safe({"jti": "p1"}) is not None
        
        m_create.side_effect = IntegrityError("a", "b", "c")
        assert await p_repo.create_safe({"jti": "p2"}) is None
        
    mock_tok_p = MagicMock(used=False)
    await p_repo.mark_used(mock_tok_p)
    assert mock_tok_p.used is True
    await p_repo.mark_used(mock_tok_p, auto_commit=False)
    
    db.execute.return_value = mock_cursor
    assert await p_repo.delete_expired_or_used() == 5
