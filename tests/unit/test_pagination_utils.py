from app.core.pagination import PaginationParams, get_pagination_params


def test_get_pagination_params_returns_valid_tuple():
    skip, limit = get_pagination_params(skip=2, limit=10)
    assert (skip, limit) == (2, 10)


def test_pagination_params_model_defaults():
    params = PaginationParams()
    assert params.skip == 0
    assert params.limit == 20

