import pytest
from app.core.pagination import PaginationParams, PageResponse, get_pagination_params
from pydantic import ValidationError

def test_pagination_params_validation():
    # Valid
    p1 = PaginationParams(skip=10, limit=50)
    assert p1.skip == 10
    assert p1.limit == 50
    
    # Defaults
    p2 = PaginationParams()
    assert p2.skip == 0
    assert p2.limit == 20
    
    # Invalid skip
    with pytest.raises(ValidationError):
        PaginationParams(skip=-1)
        
    # Invalid limit (too small)
    with pytest.raises(ValidationError):
        PaginationParams(limit=0)
        
    # Invalid limit (too large)
    with pytest.raises(ValidationError):
        PaginationParams(limit=101)

def test_page_response_envelope():
    items = ["a", "b"]
    resp = PageResponse[str](
        items=items,
        total=100,
        skip=0,
        limit=2
    )
    assert resp.items == items
    assert resp.total == 100
    assert resp.skip == 0
    assert resp.limit == 2
    
    # Invalid total
    with pytest.raises(ValidationError):
        PageResponse(items=[], total=-1)

def test_get_pagination_params_helper():
    # This covers line 136
    s, l = get_pagination_params(10, 50)
    assert s == 10
    assert l == 50
    
    # Default values
    s, l = get_pagination_params()
    assert s == 0
    assert l == 20
