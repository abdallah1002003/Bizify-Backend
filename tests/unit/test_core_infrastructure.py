"""Comprehensive tests for app/core/ to reach 100% coverage."""
import pytest
import asyncio
import time
import zlib
import pickle
import sys
import importlib
import jwt
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import timezone
from fastapi import HTTPException



from app.core.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitState, CircuitBreakerOpenError
# Initial imports for types (careful with reloads)
from app.core.cache import CacheBackend
from app.core.token_blacklist import blacklist_token, is_token_blacklisted, clear_blacklist
from app.core.encryption import encrypt, decrypt, _get_key, EncryptedString
from app.core.pagination import PageResponse, get_pagination_params
from app.core.structured_logging import (
    PerformanceTimer, get_logger, log_context, get_log_context, StructuredFormatter
)
from app.core.metrics import MetricsTimer, record_http_request, record_db_query, record_cache_operation
from app.core.exceptions import (
    AppException, ResourceNotFoundError, AuthenticationError, 
    ValidationError, AccessDeniedError, ConflictError,
    BadRequestError, ExternalServiceError, DatabaseError, InvalidStateError,
    http_exception_from_app_exception
)
from app.core.config import get_settings
from app.core.async_patterns import (
    get_chat_session_async, get_chat_sessions_by_user_async,
    create_chat_session_async, add_messages_batch_async,
    fetch_multiple_sessions_async, stream_sessions_async
)
from app.core.security import (
    create_access_token,
    create_password_reset_token, verify_password_reset_token,
    create_email_verification_token, verify_email_verification_token,
    get_password_hash, verify_password
)
from app.core.dependencies import get_current_user, require_roles, is_admin_or_self, require_admin_or_self
from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates, transactional
from app.core.event_handlers import register_all_handlers
from app.models.enums import ChatSessionType, UserRole

class AsyncContextManagerMock:
    def __init__(self, return_value=None):
        self.return_value = return_value
    async def __aenter__(self):
        return self.return_value
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

# ── Async Patterns ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_async_patterns_exhaustive():
    # Imports moved to top-level
    db = AsyncMock()
    db.begin = MagicMock(return_value=AsyncContextManagerMock(db))
    uid = uuid4()
    
    db.add = AsyncMock()
    db.add_all = AsyncMock()
    
    # Coverage for lines like db.add(...)
    await create_chat_session_async(db, uid, ChatSessionType.GENERAL)
    await add_messages_batch_async(db, uid, [{"role": "u", "content": "h"}])
    
    mock_res = MagicMock()
    mock_res.scalars().first.return_value = MagicMock(id=uid)
    db.execute.return_value = mock_res
    res = await get_chat_session_async(db, uid)
    assert res.id == uid

    mock_sessions = [MagicMock(id=uuid4()), MagicMock(id=uuid4())]
    mock_data = MagicMock()
    mock_data.scalars().all.return_value = mock_sessions
    mock_count = MagicMock()
    mock_count.scalars().all.return_value = [1, 2]
    
    with patch("asyncio.gather", new_callable=AsyncMock) as m_gather:
        m_gather.return_value = (mock_data, mock_count)
        sessions, total = await get_chat_sessions_by_user_async(db, uid)
        assert len(sessions) == 2
        assert total == 2

    with patch("app.core.async_patterns.ChatSession") as MockSession:
        MockSession.return_value = MagicMock(id=uid)
        await create_chat_session_async(db, uid, ChatSessionType.GENERAL)

    with patch("app.core.async_patterns.get_chat_session_async", new_callable=AsyncMock) as m_get:
        m_get.side_effect = [MagicMock(), Exception("fail"), MagicMock()]
        ids = [uuid4(), uuid4(), uuid4()]
        results = await fetch_multiple_sessions_async(db, ids)
        assert len(results) == 3
        assert results[1] is None

    async def mock_get_sessions(*args, **kwargs):
        if kwargs.get('skip') == 0:
            return ([MagicMock(), MagicMock()], 2)
        return ([], 2)
    with patch("app.core.async_patterns.get_chat_sessions_by_user_async", side_effect=mock_get_sessions):
        count = 0
        async for _ in stream_sessions_async(db, uid, batch_size=2):
            count += 1
        assert count == 2


# ── Caching ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cache_logic_exhaustive():
    class DummyBackend(CacheBackend):
        async def get(self, k): return await super().get(k)
        async def set(self, k, v, t=None): return await super().set(k, v, t)
        async def delete(self, k): return await super().delete(k)
        async def exists(self, k): return await super().exists(k)
        async def clear(self): return await super().clear()
        async def health_check(self): return await super().health_check()
    d = DummyBackend()
    await d.get("k")
    await d.set("k", 1)
    await d.delete("k")
    await d.exists("k")
    await d.clear()
    await d.health_check()

    # Ensure redis is present for CacheManager logic
    with patch.dict(sys.modules, {'redis': MagicMock()}):
        import app.core.cache as cache_mod
        importlib.reload(cache_mod)
        # Use classes from the reloaded module to avoid identity issues
        R_InMemoryCache = cache_mod.InMemoryCache
        R_RedisCache = cache_mod.RedisCache
        R_CacheManager = cache_mod.CacheManager
        R_get_cache_manager = cache_mod.get_cache_manager
        R_clear_cache_manager = cache_mod.clear_cache_manager

    cache = R_InMemoryCache()
    await cache.set("k", "v", ttl_seconds=10)
    assert await cache.get("k") == "v"
    
    with patch("app.core.cache.time", return_value=time.time() + 20):
        # Trigger expired branch
        assert await cache.get("k") is None
    
    await cache.set("k2", "v2")
    await cache.delete("k2")
    assert await cache.get("k2") is None
    assert await cache.health_check() is True
    await cache.clear()

    await cache.get("miss_special")
    await cache.set("hit_special", 1)
    await cache.get("hit_special")
    stats = cache.get_stats()
    assert stats["hits"] == 2
    assert stats["misses"] == 3

    with patch("redis.asyncio.Redis", new_callable=MagicMock) as MockRedis:
        mock_client = AsyncMock()
        MockRedis.return_value = mock_client
        mock_client.ping.return_value = True
        rc = R_RedisCache(host="localhost", port=6379, password="pass")
        rc._healthy = True 
        rc.client = mock_client 
        
        # Coverage for compression and pickle
        mock_client.get.return_value = pickle.dumps("v")
        assert await rc.get("k") == "v"
        
        await rc.set("large", "A" * 2000)
        set_args = mock_client.set.call_args[0]
        assert set_args[1].startswith(b"__COMPRESSED__")
        
        mock_client.get.return_value = b"__COMPRESSED__" + zlib.compress(pickle.dumps("v2"))
        assert await rc.get("large") == "v2"
        
        # Coverage for client is None branch
        rc_no_client = R_RedisCache()
        rc_no_client.client = None
        assert await rc_no_client.get("k") is None
        assert await rc_no_client.set("k", "v") is False
        assert await rc_no_client.delete("k") is False
        assert await rc_no_client.exists("k") is False
        assert await rc_no_client.clear() is False
        
        mock_client.get.side_effect = Exception("redis down")
        assert await rc.get("key") is None
        mock_client.set.side_effect = Exception("fail")
        assert await rc.set("k", "v") is False
        mock_client.delete.side_effect = Exception("fail")
        assert await rc.delete("k") is False
        mock_client.exists.side_effect = Exception("fail")
        assert await rc.exists("k") is False
        mock_client.flushdb.side_effect = Exception("fail")
        assert await rc.clear() is False
        mock_client.ping.side_effect = Exception("fail")
        assert await rc.health_check() is False
        
        with patch("redis.asyncio.Redis", side_effect=Exception("conn fail")):
            rc_fail = R_RedisCache()
            assert rc_fail.client is None
            assert rc_fail._healthy is False

    # Force Redis backend injection
    with patch("app.core.cache.RedisCache") as MockRC:
        mock_backend = MockRC.return_value
        mock_backend._healthy = True
        
        cm_redis = R_CacheManager(use_redis=True)
        cm_redis.backend = mock_backend 
        assert cm_redis.backend == mock_backend
        
        mock_backend.get = AsyncMock(return_value="v")
        mock_backend.set = AsyncMock(return_value=True)
        mock_backend.delete = AsyncMock(return_value=True)
        mock_backend.exists = AsyncMock(return_value=True)
        mock_backend.clear = AsyncMock(return_value=True)
        mock_backend.health_check = AsyncMock(return_value=True)
        
        await cm_redis.get("k")
        await cm_redis.set("k", "v")
        await cm_redis.delete("k")
        await cm_redis.exists("k")
        await cm_redis.clear()
        await cm_redis.is_healthy()

        mock_backend.client = AsyncMock()
        mock_backend.client.incr.return_value = 5
        assert await cm_redis.increment_generation_key("ns") == 5
        
        mock_backend.client.incr.side_effect = Exception("fail")
        mock_backend.get.return_value = 5
        assert await cm_redis.increment_generation_key("ns") == 6
        
        R_clear_cache_manager()

    cm = R_CacheManager(use_redis=False)
    assert isinstance(cm.backend, R_InMemoryCache)
    await cm.set("mgr", 1)
    await cm.get("mgr")
    await cm.exists("mgr")
    await cm.delete("mgr")
    await cm.clear()
    await cm.is_healthy()
    await cm.get_generation_key("ns")
    await cm.increment_generation_key("ns")
    
    @cm.setup_caching_decorator(ttl_seconds=60)
    async def cached_func(x): return x * 2
    assert await cached_func(10) == 20
    assert await cached_func(10) == 20
    
    def sync_func(): pass
    with pytest.raises(TypeError): 
        cm.setup_caching_decorator()(sync_func)

    with patch("app.core.cache.redis", None):
         assert R_get_cache_manager() is not None


# ── Circuit Breaker ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_circuit_breaker_exhaustive():
    with pytest.raises(ValueError):
        CircuitBreaker("v", config=CircuitBreakerConfig(failure_threshold=0))
    with pytest.raises(ValueError):
        CircuitBreaker("v", config=CircuitBreakerConfig(recovery_timeout_seconds=0))
    with pytest.raises(ValueError):
        CircuitBreaker("v", config=CircuitBreakerConfig(half_open_success_threshold=0))

    config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout_seconds=0.1)
    cb = CircuitBreaker("test-cb", config=config)
    async def success_fn():
        return "ok"
    async def fail_fn():
        raise ValueError("bad")
    
    assert await cb.call(success_fn) == "ok"
    # Coverage for line 69, 79-82
    with patch.object(cb, "allow_call", return_value=False):
        with pytest.raises(CircuitBreakerOpenError):
            await cb.call(success_fn)
    
    with pytest.raises(ValueError):
        await cb.call(fail_fn)
    with pytest.raises(ValueError):
        await cb.call(fail_fn)
    assert cb.state == CircuitState.OPEN
    
    assert cb._should_attempt_reset(time.monotonic()) is False
    
    cb._state = CircuitState.CLOSED
    await cb._enter_half_open_if_ready()
    cb._state = CircuitState.OPEN
    
    with pytest.raises(CircuitBreakerOpenError):
        await cb.call(success_fn)
        
    await asyncio.sleep(0.15)
    cb._state = CircuitState.HALF_OPEN
    cb._half_open_in_flight = True
    assert await cb.allow_call() is False
    cb._half_open_in_flight = False
    
    assert await cb.call(success_fn) == "ok"
    assert cb.state == CircuitState.CLOSED


# ── Token Blacklist ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_token_blacklist_exhaustive():
    clear_blacklist()
    # Coverage for memory cleanup
    with patch("app.core.token_blacklist.time.time", side_effect=[100, 300]):
        await blacklist_token("j1", 10)
        await is_token_blacklisted("j1") # expired check
    
    from app.core.token_blacklist import _get_async_redis_client
    with patch("app.core.token_blacklist.settings") as m_settings:
        m_settings.REDIS_ENABLED = False
        assert await _get_async_redis_client() is None
        
        m_settings.REDIS_ENABLED = True
        import app.core.token_blacklist as tb
        tb._redis_client = None
        with patch("redis.asyncio.Redis", side_effect=Exception("unreachable")):
            assert await tb._get_async_redis_client() is None
            
        m_settings.APP_ENV = "production"
        with patch("app.core.token_blacklist._get_async_redis_client", new_callable=AsyncMock) as m_get_rc:
            mock_client = AsyncMock()
            m_get_rc.return_value = mock_client
            mock_client.setex.side_effect = Exception("fail")
            await blacklist_token("r-fail", 100)
            
            mock_client.exists.side_effect = Exception("fail")
            assert await is_token_blacklisted("r-fail") is True


 #── Metrics ───────────────────────────────────────────────────────────────────

def test_metrics_exhaustive():
    record_http_request("GET", "/test", 200, 0.1)
    record_db_query("SELECT", "users", 0.05)
    record_cache_operation("redis", True)
    
    from app.core.metrics import (
        record_auth_attempt, record_ai_request, record_email_sent, record_error, http_request_duration_seconds
    )
    record_auth_attempt("login", True)
    record_ai_request("openai", "gpt-4", 2.0, True)
    record_email_sent("welcome", True)
    record_error("ValueError", "core")
    
    record_http_request("POST", "/api", 500, 2.0)
    record_db_query("DELETE", "sessions", 0.1, error=True)
    
    with MetricsTimer(http_request_duration_seconds, {"method": "GET", "endpoint": "/t"}):
        time.sleep(0.01)


# ── Encryption & Pagination & Utils ───────────────────────────────────────────

def test_core_utils_exhaustive():
    # Imports moved to top-level

    with patch("app.core.encryption.settings") as m_settings_enc:
        m_settings_enc.ENCRYPTION_KEY = ""
        m_settings_enc.APP_ENV = "production"
        with pytest.raises(RuntimeError):
            _get_key()
        
        m_settings_enc.APP_ENV = "development"
        m_settings_enc.ENCRYPTION_KEY = "00" * 31
        with pytest.raises(RuntimeError):
            _get_key()
        
        m_settings_enc.ENCRYPTION_KEY = "invalid hex"
        with pytest.raises(RuntimeError):
            _get_key()

    data = "hello world"
    decrypted = decrypt(encrypt(data))
    assert decrypted == data
    
    decorator = EncryptedString()
    assert decorator.process_bind_param(None, None) is None
    assert isinstance(decorator.process_bind_param("raw", None), str)
    assert decorator.process_result_value(None, None) is None
    assert decorator.process_result_value("invalid", None) == "invalid"
    # Coverage for line 84-86 (encrypted case)
    assert decorator.process_result_value(encrypt(data), None) == data

    assert get_pagination_params(5, 0) == (5, 0)
    resp = PageResponse(items=[1], total=1, skip=0, limit=1)
    assert resp.total == 1

    exs = [
        AppException("msg"), ResourceNotFoundError("U", "1"), AuthenticationError("b"),
        ValidationError("i", field="f"), AccessDeniedError("n"), ConflictError("e", conflict_field="f", existing_value="v"),
        BadRequestError("br"), ExternalServiceError("s", "o", original_error="e"),
        DatabaseError("d", entity_type="T", original_error="e"), InvalidStateError("is", current_state="A", required_state="B")
    ]
    for ex in exs:
        with pytest.raises(AppException): 
            raise ex
        assert http_exception_from_app_exception(ex) is not None

    assert get_settings() is not None


# ── Structured Logging ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_structured_logging_exhaustive():
    with patch.dict(sys.modules, {'pythonjsonlogger': None}):
        importlib.reload(sys.modules['app.core.structured_logging'])

    logger = get_logger("test")
    # Coverage for threshold_ms branch
    with PerformanceTimer(logger, "slow-op", threshold_ms=-1): 
        await asyncio.sleep(0.001)
    with PerformanceTimer(logger, "err", threshold_ms=100) as pt:
        try: 
            raise ValueError("fail")
        except Exception: 
            pt.__exit__(ValueError, ValueError("fail"), None)
    with log_context(correlation_id="root"):
        assert get_log_context().correlation_id == "root"
        with log_context(correlation_id="child"): 
            pass
        assert get_log_context().correlation_id == "root"
    
    f = StructuredFormatter()
    class MockRecord:
        def __init__(self):
            self.created = time.time()
            self.levelname = "INFO"
            self.name = "test"
            self.exc_info = None
            self.msg = "msg"
            self.args = ()
        def getMessage(self): return self.msg
    
    rec = MockRecord()
    rec.custom = 1
    rec.__dict__["custom"] = 1
    assert "custom" in f.format(rec)


# ── Security ──────────────────────────────────────────────────────────────────

def test_security_exhaustive():
    # Imports moved to top-level
    subject = "user-123"
    token = create_access_token(subject)
    token_payload = jwt.decode(token, options={"verify_signature": False})
    assert token_payload["type"] == "access"
    
    pr_token = create_password_reset_token("a@b.com")
    assert verify_password_reset_token(pr_token)["sub"] == "a@b.com"
    assert verify_password_reset_token("invalid") is None
    
    ev_token = create_email_verification_token("a@b.com")
    assert verify_email_verification_token(ev_token)["sub"] == "a@b.com"
    
    hpwd = get_password_hash("pwd")
    assert verify_password("pwd", hpwd) is True


# ── Events ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_events_exhaustive():
    with patch.dict(sys.modules, {'redis': MagicMock()}):
        import app.core.events
        importlib.reload(app.core.events)
    
    from app.core.events import EventDispatcher
    ed = EventDispatcher()
    
    h_called = []
    async def h(ev, pay): h_called.append(pay)
    ed.subscribe("ev", h)
    await ed.emit("ev", {"a": 1})
    assert len(h_called) == 1
    
    ed_redis = EventDispatcher()
    with patch("app.core.cache.get_cache_manager") as m_get_mgr_ev:
        mock_mgr = MagicMock()
        mock_rc = AsyncMock()
        mock_mgr.backend.client = mock_rc
        m_get_mgr_ev.return_value = mock_mgr
        mock_rc.publish.side_effect = Exception("fail")
        await ed_redis.emit("ev", {"a": 1})


# ── Dependency Gates ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_dependencies_exhaustive():
    db = AsyncMock()
    
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_res
    
    with patch("jwt.decode", return_value={"sub": "u", "type": "access", "jti": "j"}):
        with pytest.raises(HTTPException): 
            await get_current_user(db, "token")

    with patch("app.core.dependencies.is_token_blacklisted", return_value=True):
        with patch("jwt.decode", return_value={"sub": "u", "type": "access", "jti": "j"}):
            with pytest.raises(HTTPException): 
                await get_current_user(db, "token")

    with patch("jwt.decode") as m_decode_dep_final:
        m_decode_dep_final.return_value = {"sub": str(uuid4()), "type": "refresh", "jti": "j1"}
        with pytest.raises(HTTPException): 
            await get_current_user(db, "token")
        
        m_decode_dep_final.side_effect = jwt.PyJWTError()
        with pytest.raises(HTTPException): 
            await get_current_user(db, "invalid")
        m_decode_dep_final.side_effect = None

    mock_user = MagicMock(id=uuid4(), role=UserRole.ADMIN)
    assert is_admin_or_self(mock_user, mock_user.id) is True
    require_admin_or_self(mock_user, mock_user.id)
    
    # role check fail coverage
    with pytest.raises(HTTPException): 
        require_roles(UserRole.ADMIN)(MagicMock(role=UserRole.MENTOR))


@pytest.mark.asyncio
async def test_crud_and_handlers_exhaustive():
    assert _utc_now().tzinfo == timezone.utc
    assert _to_update_dict(None) == {}
    
    assert _apply_updates(None, {"a": 1}) is None
    
    db = MagicMock()
    with transactional(db): 
        pass
    db.commit.assert_called()
    
    db.commit.side_effect = AppException("fail")
    with pytest.raises(AppException):
        with transactional(db): 
            pass
    db.rollback.assert_called()

    with patch("app.core.event_handlers.register_email_handlers") as m_reg_h:
        register_all_handlers()
        m_reg_h.assert_called()
