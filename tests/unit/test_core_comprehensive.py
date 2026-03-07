import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.core import cache, circuit_breaker, dependencies, encryption, events, exceptions, metrics, security, token_blacklist, async_patterns
from app.core.exceptions import AppException, ResourceNotFoundError

@pytest.mark.asyncio
async def test_async_patterns_coverage():
    from app.core.async_patterns import (
        get_chat_session_async,
        get_chat_sessions_by_user_async,
        create_chat_session_async,
        add_messages_batch_async,
        fetch_multiple_sessions_async,
        update_session_summary_async,
        transfer_session_ownership_async,
        stream_sessions_async
    )
    from app.models.enums import ChatSessionType
    from uuid import uuid4
    
    db = AsyncMock()
    
    # 1. get_chat_session_async
    mock_result = MagicMock()
    mock_result.scalars().first.return_value = "session1"
    db.execute.return_value = mock_result
    res = await get_chat_session_async(db, uuid4())
    assert res == "session1"
    
    # 2. get_chat_sessions_by_user_async
    import asyncio
    async def mock_execute(stmt):
        m = MagicMock()
        m.scalars().all.return_value = ["session2"]
        return m
    db.execute = mock_execute
    res, count = await get_chat_sessions_by_user_async(db, uuid4())
    assert res == ["session2"]
    assert count == 1
    
    # 3. create_chat_session_async
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    res = await create_chat_session_async(db, uuid4(), ChatSessionType.GENERAL)
    assert res.session_type == ChatSessionType.GENERAL
    
    # 4. add_messages_batch_async
    db.add_all = MagicMock()
    res = await add_messages_batch_async(db, uuid4(), [{"role": "user", "content": "hi"}])
    assert len(res) == 1
    assert res[0].content == "hi"
    
    # 5. fetch_multiple_sessions_async
    with patch("app.core.async_patterns.get_chat_session_async", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = ["sess1", Exception("err")]
        res = await fetch_multiple_sessions_async(db, [uuid4(), uuid4()])
        assert res == ["sess1", None]
        
    # 6. update_session_summary_async
    with patch("app.core.async_patterns.get_chat_session_async", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        res = await update_session_summary_async(db, uuid4(), {})
        assert res is False
        
        mock_get.return_value = "session"
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        res = await update_session_summary_async(db, uuid4(), {})
        assert res is True
        
    # 7. transfer_session_ownership_async
    m_db = AsyncMock()
    mock_transaction = MagicMock()
    mock_transaction.__aenter__ = AsyncMock(return_value=mock_transaction)
    mock_transaction.__aexit__ = AsyncMock(return_value=None)
    m_db.begin = MagicMock(return_value=mock_transaction)
    
    with patch("app.core.async_patterns.get_chat_session_async", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        res = await transfer_session_ownership_async(m_db, uuid4(), uuid4())
        assert res is False # Rolls back on ValueError
        
        mock_get.return_value = MagicMock(user_id=uuid4())
        res = await transfer_session_ownership_async(m_db, uuid4(), uuid4())
        assert res is True
        
    # 8. stream_sessions_async
    with patch("app.core.async_patterns.get_chat_sessions_by_user_async", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = [(['s1', 's2'], 2), ([], 0)]
        items = []
        async for s in stream_sessions_async(db, uuid4()):
            items.append(s)
        assert items == ['s1', 's2']

@pytest.mark.asyncio
async def test_cache_coverage():
    from app.core.cache import (
        InMemoryCache, RedisCache, CacheManager, get_cache_manager, clear_cache_manager
    )
    import zlib, pickle
    
    # InMemoryCache
    mem = InMemoryCache()
    await mem.set("k1", "v1", ttl_seconds=10)
    assert await mem.get("k1") == "v1"
    assert await mem.exists("k1") is True
    await mem.delete("k1")
    assert await mem.get("k1") is None
    
    # Expiry
    await mem.set("k2", "v2", ttl_seconds=-10) # Expired
    assert await mem.get("k2") is None
    assert await mem.exists("k2") is False
    
    # Line 117: delete non-existent
    assert await mem.delete("non-existent") is False
    
    # Line 126-127: exists with expired key
    await mem.set("k_exp", "v", ttl_seconds=-1)
    assert await mem.exists("k_exp") is False
    
    await mem.set("k3", "v3")
    await mem.clear()
    assert await mem.get("k3") is None
    assert await mem.health_check() is True
    assert mem.get_stats()["hits"] >= 0
    assert mem.get_stats()["hit_rate"] >= 0
    
    # hit_rate with 0 total
    mem2 = InMemoryCache()
    assert mem2.get_stats()["hit_rate"] == 0
    
    # RedisCache (mocked)
    with patch("app.core.cache.redis_mod"), patch("redis.asyncio.Redis") as mock_redis_cls:
        mock_client = AsyncMock()
        mock_redis_cls.return_value = mock_client
        
        red = RedisCache(compression_threshold=10)
        
        # Test get normal
        mock_client.get.return_value = pickle.dumps("v1")
        assert await red.get("normal") == "v1"
        
        # Test get compressed
        mock_client.get.return_value = b"__COMPRESSED__" + zlib.compress(pickle.dumps("v2"))
        assert await red.get("comp") == "v2"
        
        # Test set normal
        await red.set("normal", "v1")
        mock_client.set.assert_called()
        
        # Test set compressed
        await red.set("comp", "very long string to trigger comp " * 10, ttl_seconds=10)
        mock_client.setex.assert_called()
        
        # Test exists, delete, clear, health
        mock_client.exists.return_value = 1
        assert await red.exists("k") is True
        
        mock_client.delete.return_value = 1
        assert await red.delete("k") is True
        
        mock_client.flushdb = AsyncMock()
        assert await red.clear() is True
        
        mock_client.ping = AsyncMock()
        assert await red.health_check() is True
        
        # Test error fallback (lines 211-213, 234-236, 245-247, 256-258, 268-270)
        mock_client.get.side_effect = Exception("err")
        assert await red.get("error") is None
        
        mock_client.set.side_effect = Exception("err")
        assert await red.set("error", "v") is False
        
        mock_client.delete.side_effect = Exception("err")
        assert await red.delete("error") is False
        
        mock_client.exists.side_effect = Exception("err")
        assert await red.exists("error") is False
        
        mock_client.flushdb.side_effect = Exception("err")
        assert await red.clear() is False
        
        # Test initialization failure (lines 189-192)
        mock_redis_cls.side_effect = Exception("init err")
        red_fail = RedisCache()
        assert red_fail._healthy is False
        
        # Test get None (line 205)
        mock_client.get.return_value = None
        assert await red.get("missing") is None
        
        # Test get None (line 205)
        red.client.get = AsyncMock(return_value=None)
        assert await red.get("missing") is None
        
        # Test initialization failure (lines 189-192)
        mock_redis_cls.side_effect = Exception("init err")
        red_fail = RedisCache()
        assert red_fail._healthy is False
        
        # Test broken health
        mock_client.ping = AsyncMock(side_effect=Exception("err"))
        assert await red.health_check() is False
        
        # Line 196-197: No client
        red.client = None
        assert await red.get("k") is None
        assert await red.set("k", "v") is False
        assert await red.delete("k") is False
        assert await red.exists("k") is False
        assert await red.clear() is False
        assert await red.health_check() is False
        
    # CacheManager coverage (lines 315, 327, 331, 335)
    clear_cache_manager()
    mgr_mem = CacheManager(use_redis=False)
    assert isinstance(mgr_mem.backend, InMemoryCache)
    
    await mgr_mem.set("k", "v")
    assert await mgr_mem.exists("k") is True
    assert await mgr_mem.delete("k") is True
    await mgr_mem.clear()
    
    # Coverage for abstract base methods (lines 42, 47, 52, 57, 62, 67)
    from app.core.cache import CacheBackend
    class MockBackend(CacheBackend):
        async def get(self, k): return await super().get(k)
        async def set(self, k, v, t=None): return await super().set(k, v, t)
        async def delete(self, k): return await super().delete(k)
        async def exists(self, k): return await super().exists(k)
        async def clear(self): return await super().clear()
        async def health_check(self): return await super().health_check()
    
    mb = MockBackend()
    await mb.get("k"); await mb.set("k", "v"); await mb.delete("k"); await mb.exists("k"); await mb.clear(); await mb.health_check()
        
    # CacheManager coverage (lines 315, 327, 331, 335)
    clear_cache_manager()
    mgr_mem = CacheManager(use_redis=False)
    assert isinstance(mgr_mem.backend, InMemoryCache)
    
    await mgr_mem.set("k", "v")
    assert await mgr_mem.exists("k") is True
    assert await mgr_mem.delete("k") is True
    await mgr_mem.clear()
        
    # CacheManager
    clear_cache_manager()
    with patch("app.core.cache.redis_mod"), patch("app.core.cache.RedisCache") as mock_rc:
        mock_rc.return_value._healthy = True
        mock_rc.return_value.client = AsyncMock()
        mock_rc.return_value.client.incr.return_value = 5
        
        mgr = get_cache_manager(use_redis=True)
        assert mgr.backend is mock_rc.return_value
        
        # Ensure backend methods and client methods are AsyncMocks
        mgr.backend.get = AsyncMock(return_value=None)
        mgr.backend.set = AsyncMock(return_value=True)
        mgr.backend.client.incr = AsyncMock(return_value=5)
        mgr.backend.health_check = AsyncMock(return_value=True)
        
        assert await mgr.increment_generation_key("ns") == 5
        assert await mgr.is_healthy() is True
        
        # get_generation_key (lines 339-343)
        mgr.backend.get.return_value = None
        gen = await mgr.get_generation_key("new_ns")
        assert gen == 0
        
        # increment_generation_key fallback (lines 352-359)
        mock_rc.return_value.client.incr.side_effect = Exception("redis err")
        mgr.backend.get.return_value = 10
        new_gen = await mgr.increment_generation_key("ns")
        assert new_gen == 11
        
        # Decorator
        dec = mgr.setup_caching_decorator()
        
        @dec
        async def dummy_func(x):
            return x * 2
            
        mgr.backend.get.return_value = None
        mgr.backend.get.side_effect = None
        mgr.backend.set = AsyncMock(return_value=True)
        
        assert await dummy_func(5) == 10
        mgr.backend.get.return_value = 10
        assert await dummy_func(5) == 10  # Cache hit
        
        # Line 373-374: TypeError if not coroutine
        def sync_func(): pass
        with pytest.raises(TypeError):
            dec(sync_func)
            
    # get_cache_manager logic (lines 418-425)
    clear_cache_manager()
    with patch("app.core.cache.settings") as mock_settings:
        mock_settings.REDIS_HOST = "h"
        mock_settings.REDIS_PORT = 123
        mock_settings.REDIS_PASSWORD = "p"
        mock_settings.REDIS_ENABLED = True
        
        m = get_cache_manager()
        assert m is not None
        clear_cache_manager()
        
    # Line 312-313: Fallback during CacheManager init
    with patch("app.core.cache.RedisCache") as mock_rc:
        mock_rc.return_value._healthy = False
        mgr_fb = CacheManager(use_redis=True)
        assert isinstance(mgr_fb.backend, InMemoryCache)

@pytest.mark.asyncio
async def test_circuit_breaker_coverage():
    from app.core.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitState, CircuitBreakerOpenError
    
    cb = CircuitBreaker("test", config=CircuitBreakerConfig(
        failure_threshold=2,
        recovery_timeout_seconds=0.1,
        half_open_success_threshold=1
    ))
    
    # 1. Successful call
    async def ok_call(): return "ok"
    assert await cb.call(ok_call) == "ok"
    assert cb.state == CircuitState.CLOSED
    
    # 2. Failures
    async def fail_call(): raise ValueError("err")
    with pytest.raises(ValueError):
        await cb.call(fail_call)
        
    assert cb.state == CircuitState.CLOSED # 1 failure, threshold=2
    
    with pytest.raises(ValueError):
        await cb.call(fail_call)
        
    assert cb.state == CircuitState.OPEN # 2 failures -> open
    
    # 3. Call while open -> fails fast
    with pytest.raises(CircuitBreakerOpenError):
        await cb.call(ok_call)
        
    # Wait for recovery timeout
    import asyncio
    await asyncio.sleep(0.15)
    
    # 4. Half-open transition and success
    assert await cb.call(ok_call) == "ok"
    assert cb.state == CircuitState.CLOSED
    
    # 5. Half-open transition and failure
    cb._opened_at = 0 # Force recovery timeout
    cb._state = CircuitState.OPEN
    with pytest.raises(ValueError):
        await cb.call(fail_call)
    assert cb.state == CircuitState.OPEN
    
    # 6. Half-open in flight rejection
    cb._opened_at = 0
    cb._state = CircuitState.OPEN
    
    # Line 69, 75: Coverage for early returns when CLOSED
    cb_closed = CircuitBreaker("closed")
    assert cb_closed._should_attempt_reset(0) is False
    await cb_closed._enter_half_open_if_ready()
    
    async def slow_call():
        await asyncio.sleep(0.01)
        return "slow"
        
    # Start slow call (enters half-open)
    # First we need to make sure we are not already OPEN with a recent timestamp
    cb._opened_at = 0
    cb._state = CircuitState.OPEN
    task = asyncio.create_task(cb.call(slow_call))
    
    # Ensure it yielded to event loop so cb._state is HALF_OPEN and in_flight is True
    await asyncio.sleep(0.001)
    
    # Second call rejected while half-open in flight
    with pytest.raises(CircuitBreakerOpenError):
        await cb.call(ok_call)
        
    await task
    assert cb.state == CircuitState.CLOSED
    
    # Invalid config
    with pytest.raises(ValueError):
        CircuitBreaker("test2", config=CircuitBreakerConfig(failure_threshold=0))
    with pytest.raises(ValueError):
        CircuitBreaker("test2", config=CircuitBreakerConfig(recovery_timeout_seconds=0))
    with pytest.raises(ValueError):
        CircuitBreaker("test2", config=CircuitBreakerConfig(half_open_success_threshold=0))

@pytest.mark.asyncio
async def test_encryption_coverage():
    from app.core.encryption import encrypt, decrypt, _get_key, EncryptedString
    from config.settings import settings
    
    old_env = settings.APP_ENV
    old_key = getattr(settings, "ENCRYPTION_KEY", "")
    
    # Test valid key
    settings.ENCRYPTION_KEY = "00" * 32
    enc = encrypt("hello world")
    assert decrypt(enc) == "hello world"
    
    # EncryptedString
    TypeDec = EncryptedString()
    assert TypeDec.process_bind_param(None, None) is None
    bound = TypeDec.process_bind_param("secret", None)
    assert bound != "secret"
    
    assert TypeDec.process_result_value(None, None) is None
    assert TypeDec.process_result_value(bound, None) == "secret"
    
    # Bad decryption falls back to raw value (legacy)
    assert TypeDec.process_result_value("not-base64-or-bad", None) == "not-base64-or-bad"
    
    # Line 37: Empty key in test env
    settings.APP_ENV = "test"
    settings.ENCRYPTION_KEY = ""
    assert _get_key() == bytes.fromhex("00" * 32)
    
    # Bad config exceptions
    settings.APP_ENV = "prod"
    settings.ENCRYPTION_KEY = ""
    with pytest.raises(RuntimeError, match="ENCRYPTION_KEY is not set"):
        _get_key()
        
    settings.ENCRYPTION_KEY = "not-hex"
    with pytest.raises(RuntimeError):
        _get_key()
        
    settings.ENCRYPTION_KEY = "00" * 16 # Short
    with pytest.raises(RuntimeError):
        _get_key()
        
    settings.APP_ENV = old_env
    settings.ENCRYPTION_KEY = old_key

@pytest.mark.asyncio
async def test_security_coverage():
    from app.core.security import (
        create_access_token, create_refresh_token, create_password_reset_token,
        verify_password_reset_token, verify_password, get_password_hash,
        create_email_verification_token, verify_email_verification_token
    )
    from datetime import timedelta
    
    # Access/Refresh tokens
    sub = "user123"
    t1 = create_access_token(sub)
    t1_delta = create_access_token(sub, expires_delta=timedelta(minutes=5))
    assert t1 != t1_delta
    
    t2 = create_refresh_token(sub)
    t2_delta = create_refresh_token(sub, expires_delta=timedelta(days=1))
    assert t2 != t2_delta
    
    # Password Reset
    email = "test@example.com"
    pr_token = create_password_reset_token(email)
    payload = verify_password_reset_token(pr_token)
    assert payload["sub"] == email
    assert payload["type"] == "password_reset"
    
    # Invalid reset token
    assert verify_password_reset_token("invalid") is None
    
    # Wrong type reset token
    wrong_type_token = create_access_token(sub)
    assert verify_password_reset_token(wrong_type_token) is None
    
    # Email Verification
    ev_token = create_email_verification_token(email)
    payload = verify_email_verification_token(ev_token)
    assert payload["sub"] == email
    assert payload["type"] == "email_verification"
    
    # Invalid email token
    assert verify_email_verification_token("invalid") is None
    assert verify_email_verification_token(pr_token) is None # Wrong type
    
    # Password hashing
    pwd = "secret-password"
    hashed = get_password_hash(pwd)
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrong", hashed) is False

@pytest.mark.asyncio
async def test_events_coverage():
    from app.core.events import EventDispatcher, CustomJSONEncoder
    from uuid import uuid4
    import datetime
    
    # CustomJSONEncoder
    enc = CustomJSONEncoder()
    u = uuid4()
    d = datetime.datetime.now()
    assert enc.default(u) == str(u)
    assert enc.default(d) == d.isoformat()
    with pytest.raises(TypeError):
        enc.default(object())
        
    disp = EventDispatcher()
    
    called = []
    async def handler(et, p):
        called.append((et, p))
        
    disp.subscribe("test_event", handler)
    disp.subscribe("test_event", handler) # Deduplicate test
    
    from config.settings import settings
    old_env = settings.APP_ENV
    
    # Test fallback
    settings.APP_ENV = "test"
    await disp.emit("test_event", {"data": 1})
    assert len(called) == 1
    assert called[0] == ("test_event", {"data": 1})
    
    # Test Redis config behavior
    settings.APP_ENV = "prod"
    with patch("app.core.events.get_cache_manager") as mock_cm:
        # Mock redis available
        mock_client = AsyncMock()
        mock_cm.return_value.backend.client = mock_client
        
        await disp.emit("test_event", {"data": 2})
        mock_client.lpush.assert_called()
        
        # Mock redis err, tests inline fallback
        mock_client.lpush.side_effect = Exception("err")
        await disp.emit("test_event", {"data": 3})
        assert len(called) == 2
        assert called[-1][1]["data"] == 3
        
        # Line 77: event_type not in handlers
        await disp._run_handlers("no_handler", {})
        
    settings.APP_ENV = old_env
    disp.clear_all_handlers()

@pytest.mark.asyncio
async def test_exceptions_coverage():
    from app.core.exceptions import (
        AppException, ValidationError, ResourceNotFoundError, 
        AccessDeniedError, AuthenticationError, BadRequestError, 
        ConflictError, ExternalServiceError, DatabaseError, InvalidStateError,
        http_exception_from_app_exception
    )
    
    e1 = AppException("test", "CODE", {"some": "detail"}, 500)
    assert e1.message == "test"
    assert e1.code == "CODE"
    
    e2 = ValidationError("val", "field", {"d": 1})
    assert e2.details["field"] == "field"
    
    e3 = ResourceNotFoundError("User", "u1", {"d": 1})
    assert e3.details["resource_type"] == "User"
    
    e4 = AccessDeniedError("read", "User", {"d": 1})
    assert e4.details["action"] == "read"
    
    e5 = AuthenticationError("auth", {"d": 1})
    assert e5.code == "UNAUTHORIZED"
    
    e6 = BadRequestError("bad", {"d": 1})
    assert e6.code == "BAD_REQUEST"
    
    e7 = ConflictError("con", "val1", "f1", {"d": 1})
    assert e7.details["conflict_field"] == "val1"
    assert e7.details["existing_value"] == "f1"
    
    # ExternalServiceError (lines 234-244)
    e8 = ExternalServiceError("Stripe", "charge", "card declined")
    assert "charge failed: card declined" in e8.message
    assert e8.details["service"] == "Stripe"
    
    # DatabaseError (lines 273-284)
    e9 = DatabaseError("update", "User", "deadlock")
    assert "Database update failed for User: deadlock" in e9.message
    
    # InvalidStateError (lines 316-321)
    e10 = InvalidStateError("Bad state", current_state="A", required_state="B")
    assert e10.details["current_state"] == "A"
    
    # http_exception_from_app_exception (line 338)
    from fastapi import HTTPException
    hexp = http_exception_from_app_exception(e1)
    assert isinstance(hexp, HTTPException)
    assert hexp.status_code == 500

@pytest.mark.asyncio
async def test_metrics_coverage():
    from app.core import metrics
    from app.core.metrics import MetricsTimer, REGISTRY
    
    # Record functions
    metrics.record_http_request("GET", "/test", 200, 0.1)
    metrics.record_db_query("SELECT", "users", 0.05, error=True)
    metrics.record_cache_operation("redis", hit=True)
    metrics.record_cache_operation("redis", hit=False)
    metrics.record_auth_attempt("jwt", success=True)
    metrics.record_ai_request("openai", "gpt-4", 1.5, success=True)
    metrics.record_email_sent("welcome", success=True)
    metrics.record_error("ValueError", "test-service")
    
    # MetricsTimer
    hist = metrics.http_request_duration_seconds
    with MetricsTimer(hist, {"method": "POST", "endpoint": "/timer"}):
        pass # Line 248-258
    
    # Ensure registry is sane
    assert REGISTRY is not None

@pytest.mark.asyncio
async def test_structured_logging_coverage():
    from app.core import structured_logging
    from app.core.structured_logging import (
        LogContext, StructuredFormatter, log_context, 
        PerformanceTimer, get_logger, configure_structured_logging
    )
    import logging
    
    # configure_structured_logging
    configure_structured_logging("DEBUG")
    
    logger = get_logger("test_logger")
    
    # log_context (including nesting lines 125-128)
    with log_context(correlation_id="c1", user_id="u1"):
        ctx = structured_logging.get_log_context()
        assert ctx.correlation_id == "c1"
        logger.info("test log with context") # Line 52
        
        with log_context(correlation_id="c2"):
            assert structured_logging.get_log_context().correlation_id == "c2"
        
        # After nest, should be c1
        assert structured_logging.get_log_context().correlation_id == "c1"
    
    # after log_context, it should be cleared
    assert structured_logging.get_log_context() is None
    
    # Formatter with extra fields and exc_info
    formatter = StructuredFormatter()
    
    # Line 51-52: get_log_context is None (already verified it's None)
    record_no_ctx = logging.LogRecord("name", logging.INFO, "path", 10, "msg", (), None)
    out_no_ctx = formatter.format(record_no_ctx)
    assert "correlation_id" not in out_no_ctx
    
    record = logging.LogRecord("name", logging.INFO, "path", 10, "msg", (), None)
    record.custom_field = "custom_val"
    
    # Normal format
    out = formatter.format(record)
    assert "custom_val" in out
    
    # With exception (line 55-56)
    try:
        raise ValueError("test err")
    except ValueError:
        import sys
        record.exc_info = sys.exc_info()
        out_err = formatter.format(record)
        assert "exception" in out_err
        assert "test err" in out_err

    # PerformanceTimer (lines 170-179)
    # 1. Success
    with PerformanceTimer(logger, "op1", threshold_ms=10):
        pass
    
    # 2. Slow operation (line 175-179)
    with PerformanceTimer(logger, "slow_op", threshold_ms=0):
        import time
        time.sleep(0.001)
        
    # 3. Exception (line 170-174)
    try:
        with PerformanceTimer(logger, "fail_op"):
            raise RuntimeError("op failed")
    except RuntimeError:
        pass







@pytest.mark.asyncio
async def test_token_blacklist_coverage():
    from app.core import token_blacklist
    from app.core.token_blacklist import _memory_store
    from config.settings import settings
    
    # Instead of clear_blacklist which doesn't exist, we just start fresh
    _memory_store.clear()
    
    # Test memory blacklist directly
    token_blacklist._memory_blacklist("jti1", 10)
    assert token_blacklist._memory_is_blacklisted("jti1") is True
    
    token_blacklist._memory_blacklist("jti2", -10)
    assert token_blacklist._memory_is_blacklisted("jti2") is False
    
    # Public API with test env
    old_env = settings.APP_ENV
    settings.APP_ENV = "test"
    
    await token_blacklist.blacklist_token("jti3", 10)
    assert await token_blacklist.is_token_blacklisted("jti3") is True
    
    # <= 0 ttl
    await token_blacklist.blacklist_token("jti4", 0)
    assert await token_blacklist.is_token_blacklisted("jti4") is False
    
    # Redis integration mock
    settings.APP_ENV = "prod"
    settings.REDIS_ENABLED = True
    
    with patch("app.core.token_blacklist._get_async_redis_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        
        # Test set
        await token_blacklist.blacklist_token("jti5", 10)
        mock_client.setex.assert_called_with("jti_blacklist:jti5", 10, "1")
        
        # Test get
        mock_client.exists.return_value = 1
        assert await token_blacklist.is_token_blacklisted("jti5") is True
        
        # Success with Redis read (already tested with jti5)
        
        # Line 107-110: Redis write exception (surgical)
        token_blacklist._redis_client = AsyncMock()
        token_blacklist._redis_client.setex.side_effect = Exception("err")
        token_blacklist._memory_store.clear()
        await token_blacklist.blacklist_token("jti_write_err", 10)
        assert token_blacklist._memory_is_blacklisted("jti_write_err") is True
        
        # Line 132-135: Redis read exception (surgical)
        token_blacklist._redis_client.exists.side_effect = Exception("err")
        token_blacklist._memory_blacklist("jti_read_err", 10)
        assert await token_blacklist.is_token_blacklisted("jti_read_err") is True
        
    # Cleanup and hit Line 53-54, 57, 71-74
    token_blacklist._redis_client = None
    settings.REDIS_ENABLED = False
    assert await token_blacklist._get_async_redis_client() is None # Line 54
    
    settings.REDIS_ENABLED = True
    with patch("redis.asyncio.Redis") as mock_r:
        mock_inst = AsyncMock()
        mock_r.return_value = mock_inst
        # Line 70 (first init)
        c1 = await token_blacklist._get_async_redis_client()
        assert c1 is mock_inst
        # Line 57 (cached)
        c2 = await token_blacklist._get_async_redis_client()
        assert c2 is mock_inst
        
        # Line 71-74 (init failure)
        token_blacklist._redis_client = None
        mock_r.side_effect = Exception("fail")
        assert await token_blacklist._get_async_redis_client() is None

    settings.APP_ENV = old_env
    token_blacklist._redis_client = None

@pytest.mark.asyncio
async def test_dependencies_coverage():
    from app.core.dependencies import get_current_user, get_current_active_user, require_roles, require_admin, is_admin_or_self, require_admin_or_self
    from app.models.enums import UserRole
    from fastapi import HTTPException
    from config.settings import settings
    from uuid import uuid4
    import jwt
    import time
    
    # 1. get_current_user
    db = AsyncMock()
    
    # Valid token
    sub = uuid4()
    valid_token = jwt.encode({"sub": str(sub), "type": "access"}, settings.jwt_verify_key, algorithm=settings.jwt_algorithm)
    
    mock_result = MagicMock()
    mock_user = MagicMock(id=sub, is_active=True, is_verified=True, role=UserRole.ADMIN)
    mock_result.scalar_one_or_none.return_value = mock_user
    db.execute.return_value = mock_result
    
    user = await get_current_user(db, valid_token)
    assert user == mock_user
    
    # Refresh token error
    refresh_token = jwt.encode({"sub": str(sub), "type": "refresh"}, settings.jwt_verify_key, algorithm=settings.jwt_algorithm)
    with pytest.raises(HTTPException, match="Refresh token cannot be used"):
        await get_current_user(db, refresh_token)
        
    # Blacklisted token
    with patch("app.core.dependencies.is_token_blacklisted", new_callable=AsyncMock) as mock_blacklisted:
        mock_blacklisted.return_value = True
        bl_token = jwt.encode({"sub": str(sub), "jti": "bad", "type": "access"}, settings.jwt_verify_key, algorithm=settings.jwt_algorithm)
        with pytest.raises(HTTPException, match="Token has been revoked"):
            await get_current_user(db, bl_token)
            
    # Missing sub
    no_sub_token = jwt.encode({"type": "access", "jti": "j"}, settings.jwt_verify_key, algorithm=settings.jwt_algorithm)
    with pytest.raises(HTTPException, match="Could not validate credentials"):
        await get_current_user(db, no_sub_token)
        
    # Invalid JWT signature
    bad_sig_token = jwt.encode({"sub": str(sub)}, "wrong_key", algorithm="HS256")
    with pytest.raises(HTTPException, match="Could not validate credentials"):
        await get_current_user(db, bad_sig_token)
        
    # User not found in DB
    mock_result.scalar_one_or_none.return_value = None
    with pytest.raises(HTTPException, match="Could not validate credentials"):
        await get_current_user(db, valid_token)
        
    # 2. get_current_active_user
    u_active = MagicMock(is_active=True, is_verified=True)
    assert get_current_active_user(u_active) == u_active
    
    u_inactive = MagicMock(is_active=False)
    with pytest.raises(HTTPException, match="Inactive user"):
        get_current_active_user(u_inactive)
        
    old_env = settings.APP_ENV
    settings.APP_ENV = "prod"
    u_unverified = MagicMock(is_active=True, is_verified=False)
    with pytest.raises(HTTPException, match="Email not verified"):
        get_current_active_user(u_unverified)
    settings.APP_ENV = old_env
    
    # 3. RBAC helpers
    u_admin = MagicMock(role=UserRole.ADMIN, id=uuid4())
    u_user = MagicMock(role=UserRole.ENTREPRENEUR, id=uuid4())
    
    req_admin = require_roles(UserRole.ADMIN)
    assert req_admin(u_admin) == u_admin
    with pytest.raises(HTTPException, match="Required role: admin"):
        req_admin(u_user)
        
    # is_admin_or_self
    assert is_admin_or_self(u_admin, uuid4()) is True
    assert is_admin_or_self(u_user, u_user.id) is True
    assert is_admin_or_self(u_user, uuid4()) is False
    
    # require_admin_or_self
    require_admin_or_self(u_admin, uuid4()) # Shouldn't raise
    with pytest.raises(HTTPException, match="Access denied"):
        require_admin_or_self(u_user, uuid4())

@pytest.mark.asyncio
async def test_pagination_coverage():
    from app.core.pagination import get_pagination_params, PaginationParams, PageResponse
    
    # get_pagination_params (line 136)
    assert get_pagination_params(1, 2) == (1, 2)
    
    # PaginationParams pydantic
    p = PaginationParams(skip=5, limit=50)
    assert p.skip == 5
    
    # PageResponse
    pr = PageResponse(items=[1, 2, 3], total=10, skip=0, limit=3)
    assert pr.total == 10

@pytest.mark.asyncio
async def test_crud_utils_coverage():
    from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates, transactional
    from pydantic import BaseModel
    import datetime
    
    # _utc_now (line 38)
    now = _utc_now()
    assert isinstance(now, datetime.datetime)
    assert now.tzinfo == datetime.timezone.utc
    
    # _to_update_dict (lines 71-75)
    assert _to_update_dict(None) == {}
    
    class TestModel(BaseModel):
        a: int = 1
        b: str = None
    
    m = TestModel(a=2)
    assert _to_update_dict(m) == {"a": 2} # Excludes unset b
    
    assert _to_update_dict({"x": 1}) == {"x": 1}
    
    # _apply_updates (lines 104-107)
    class FakeObj:
        def __init__(self):
            self.a = 0
            self.b = 0
    
    obj = FakeObj()
    _apply_updates(obj, {"a": 1, "c": 3}) # c should be ignored
    assert obj.a == 1
    assert not hasattr(obj, "c")
    
    # transactional (lines 129-134)
    db = MagicMock()
    with transactional(db):
        pass
    db.commit.assert_called_once()
    
    db.commit.reset_mock()
    db.rollback = MagicMock()
    try:
        with transactional(db):
            raise ValueError("rollback me")
    except ValueError:
        pass
    db.rollback.assert_called_once()
    db.commit.assert_not_called()

@pytest.mark.asyncio
async def test_event_handlers_coverage():
    with patch("app.core.event_handlers.register_idea_version_handlers"), \
         patch("app.core.event_handlers.register_business_roadmap_handlers"), \
         patch("app.core.event_handlers.register_business_collaborator_handlers"), \
         patch("app.core.event_handlers.register_email_handlers"):
        from app.core.event_handlers import register_all_handlers
        register_all_handlers() # Lines 11-23

@pytest.mark.asyncio
async def test_config_coverage():
    from app.core.config import get_settings
    from config.settings import Settings
    assert isinstance(get_settings(), Settings)
