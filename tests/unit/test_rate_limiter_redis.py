import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request
from app.middleware.rate_limiter_redis import RedisRateLimiterMiddleware

@pytest.fixture
def middleware():
    app = MagicMock()
    return RedisRateLimiterMiddleware(app, requests_per_minute=10)

@pytest.mark.asyncio
async def test_get_client_ip(middleware):
    request = MagicMock(spec=Request)
    request.client.host = "192.168.1.1"
    assert middleware._get_client_ip(request) == "192.168.1.1"
    
    request.client = None
    assert middleware._get_client_ip(request) == "127.0.0.1"

@pytest.mark.asyncio
async def test_check_rate_limit_memory(middleware):
    client_ip = "127.0.0.1"
    limit = 2
    
    # 1st request
    allowed, remaining = await middleware._check_rate_limit_memory(client_ip, limit)
    assert allowed is True
    assert remaining == 2
    
    # 2nd request
    allowed, remaining = await middleware._check_rate_limit_memory(client_ip, limit)
    assert allowed is True
    assert remaining == 1
    
    # 3rd request (blocked)
    allowed, remaining = await middleware._check_rate_limit_memory(client_ip, limit)
    assert allowed is False
    assert remaining == 0

@pytest.mark.asyncio
async def test_check_rate_limit_redis_success(middleware):
    middleware.redis_client = MagicMock() # Use MagicMock for client
    middleware._redis_available = True
    
    # pipeline() returns an AsyncMock which acts as a context manager (if needed) or just returns self
    # but here it's used as pipe = self.redis_client.pipeline()
    pipe = MagicMock() # pipeline is sync in redis-py (usually) but let's check
    # Wait, in the code it's: pipe = self.redis_client.pipeline()
    middleware.redis_client.pipeline.return_value = pipe
    
    pipe.zremrangebyscore.return_value = pipe
    pipe.zadd.return_value = pipe
    pipe.zcard.return_value = pipe
    pipe.expire.return_value = pipe
    
    # execute() is awaited
    pipe.execute = AsyncMock(return_value=[0, 1, 1, True])
    
    allowed, remaining, limit = await middleware._check_rate_limit_redis("user1", "/api/v1/auth/login")
    assert allowed is True
    assert remaining == 4 # limit 5, count 1
    assert limit == 5

@pytest.mark.asyncio
async def test_check_rate_limit_redis_fallback(middleware):
    middleware.redis_client = MagicMock()
    middleware.redis_client.pipeline.side_effect = Exception("Redis Down")
    middleware._redis_available = True
    
    # Internal _check_rate_limit_memory will be called
    allowed, remaining, limit = await middleware._check_rate_limit_redis("user1", "/api/v1/resource")
    assert allowed is True
    assert remaining == 10 # limit 10, count 0 (before append)
    assert middleware._redis_available is False

@pytest.mark.asyncio
async def test_dispatch_allowed(middleware):
    request = MagicMock(spec=Request)
    request.url.path = "/api/v1/resource"
    request.client.host = "127.0.0.1"
    request.headers = {}
    
    call_next = AsyncMock()
    response = MagicMock()
    response.headers = {}
    call_next.return_value = response
    
    with patch("app.middleware.rate_limiter_redis.settings") as mock_settings:
        mock_settings.APP_ENV = "production"
        mock_settings.RATE_LIMIT_PER_MINUTE = 10
        
        middleware._init_redis = AsyncMock()
        middleware._redis_available = False # use memory
        
        resp = await middleware.dispatch(request, call_next)
        assert resp == response
        assert "X-RateLimit-Limit" in resp.headers

@pytest.mark.asyncio
async def test_dispatch_blocked(middleware):
    request = MagicMock(spec=Request)
    request.url.path = "/api/v1/auth/login"
    request.client.host = "127.0.0.1"
    request.headers = {}
    
    call_next = AsyncMock()
    
    with patch("app.middleware.rate_limiter_redis.settings") as mock_settings:
        mock_settings.APP_ENV = "production"
        mock_settings.RATE_LIMIT_PER_MINUTE = 1 
        
        middleware._init_redis = AsyncMock()
        middleware._redis_available = False
        
        # 1st allowed
        await middleware.dispatch(request, call_next)
        
        # 2nd blocked (for login, limit is 5)
        for _ in range(4):
            await middleware.dispatch(request, call_next)
            
        resp = await middleware.dispatch(request, call_next)
        assert resp.status_code == 429
