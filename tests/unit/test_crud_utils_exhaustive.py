import pytest
from datetime import datetime, timezone
from pydantic import BaseModel
from unittest.mock import MagicMock
from app.core.crud_utils import (
    _utc_now,
    _to_update_dict,
    _apply_updates,
    transactional,
)

def test_utc_now():
    now = _utc_now()
    assert isinstance(now, datetime)
    assert now.tzinfo == timezone.utc

def test_to_update_dict_pydantic():
    class TestModel(BaseModel):
        name: str = "default"
        age: int = None
    
    # Case: all set
    m1 = TestModel(name="John", age=30)
    assert _to_update_dict(m1) == {"name": "John", "age": 30}
    
    # Case: only name set
    m2 = TestModel(name="Jane")
    assert _to_update_dict(m2) == {"name": "Jane"} # age excluded as unset

def test_to_update_dict_plain_dict():
    d = {"a": 1, "b": 2}
    assert _to_update_dict(d) == d

def test_to_update_dict_none():
    assert _to_update_dict(None) == {}

def test_to_update_dict_other_obj():
    class TinyObj:
        def __init__(self):
            self.x = 1
        def __iter__(self):
            yield ("x", self.x)
            
    obj = TinyObj()
    assert _to_update_dict(obj) == {"x": 1}

def test_apply_updates():
    class Dummy:
        def __init__(self):
            self.a = 1
            self.b = 2
            
    obj = Dummy()
    updates = {"a": 10, "c": 30} # c does not exist
    
    result = _apply_updates(obj, updates)
    assert result is obj
    assert obj.a == 10
    assert obj.b == 2
    assert not hasattr(obj, "c")

def test_transactional_success():
    db = MagicMock()
    with transactional(db) as d:
        assert d == db
        # do work
    
    db.commit.assert_called_once()
    assert not db.rollback.called

def test_transactional_failure():
    db = MagicMock()
    with pytest.raises(ValueError, match="boom"):
        with transactional(db):
            raise ValueError("boom")
            
    db.rollback.assert_called_once()
    assert not db.commit.called
