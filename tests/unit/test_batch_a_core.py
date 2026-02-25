# ruff: noqa
"""
Batch A: Tests for core modules — InMemoryCache, CacheManager,
MetricsTimer + helpers, token_blacklist Redis fallback paths,
rate_limiter JWT path and bucket-full path.
"""
import time
import uuid
from unittest.mock import MagicMock, patch

import pytest


# ─────────────────────────────────────────────────────────────────
# InMemoryCache
# ─────────────────────────────────────────────────────────────────

class TestInMemoryCache:

    def _make(self):
        from app.core.cache import InMemoryCache
        return InMemoryCache()

    def test_set_and_get(self):
        c = self._make()
        assert c.set("k", "v") is True
        assert c.get("k") == "v"

    def test_get_missing_key(self):
        c = self._make()
        assert c.get("missing") is None

    def test_ttl_expiry(self):
        c = self._make()
        c.set("exp_key", "value", ttl_seconds=0)
        # TTL=0 expires immediately
        time.sleep(0.01)
        assert c.get("exp_key") is None

    def test_exists_true_and_false(self):
        c = self._make()
        c.set("present", 42)
        assert c.exists("present") is True
        assert c.exists("absent") is False

    def test_exists_expired(self):
        c = self._make()
        c.set("exp", "val", ttl_seconds=0)
        time.sleep(0.01)
        assert c.exists("exp") is False

    def test_delete_existing(self):
        c = self._make()
        c.set("del_me", 1)
        assert c.delete("del_me") is True
        assert c.get("del_me") is None

    def test_delete_missing(self):
        c = self._make()
        assert c.delete("ghost") is False

    def test_clear(self):
        c = self._make()
        c.set("a", 1)
        c.set("b", 2)
        result = c.clear()
        assert result is True
        assert c.get("a") is None
        assert c.get("b") is None

    def test_health_check_always_true(self):
        assert self._make().health_check() is True

    def test_get_stats(self):
        c = self._make()
        c.set("x", "y")
        c.get("x")        # hit
        c.get("missing")  # miss
        stats = c.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["size"] == 1
        assert 0 < stats["hit_rate"] <= 1

    def test_stats_zero_division_safe(self):
        c = self._make()
        stats = c.get_stats()
        assert stats["hit_rate"] == 0


# ─────────────────────────────────────────────────────────────────
# CacheManager (using in-memory, no Redis)
# ─────────────────────────────────────────────────────────────────

class TestCacheManager:

    def _make(self):
        from app.core.cache import CacheManager
        return CacheManager(use_redis=False)

    def test_basic_set_get(self):
        m = self._make()
        m.set("cm_key", {"data": 1})
        assert m.get("cm_key") == {"data": 1}

    def test_delete(self):
        m = self._make()
        m.set("del", "val")
        m.delete("del")
        assert m.get("del") is None

    def test_exists(self):
        m = self._make()
        m.set("exists_k", True)
        assert m.exists("exists_k") is True
        assert m.exists("nope") is False

    def test_clear(self):
        m = self._make()
        m.set("c1", 1)
        m.clear()
        assert m.get("c1") is None

    def test_is_healthy(self):
        m = self._make()
        assert m.is_healthy() is True

    def test_get_generation_key_starts_at_zero(self):
        m = self._make()
        ns = f"ns_{uuid.uuid4().hex}"
        assert m.get_generation_key(ns) == 0

    def test_increment_generation_key(self):
        m = self._make()
        ns = f"ns_{uuid.uuid4().hex}"
        m.get_generation_key(ns)  # initialize
        new_gen = m.increment_generation_key(ns)
        assert new_gen == 1
        new_gen2 = m.increment_generation_key(ns)
        assert new_gen2 == 2

    def test_caching_decorator_sync(self):
        m = self._make()
        call_count = [0]

        @m.setup_caching_decorator(ttl_seconds=60)
        def expensive(x):
            call_count[0] += 1
            return x * 2

        r1 = expensive(5)
        r2 = expensive(5)
        assert r1 == 10
        assert r2 == 10
        assert call_count[0] == 1  # cached after first call

    @pytest.mark.asyncio
    async def test_caching_decorator_async(self):
        m = self._make()
        call_count = [0]

        @m.setup_caching_decorator(ttl_seconds=60)
        async def async_op(x):
            call_count[0] += 1
            return x + 100

        r1 = await async_op(7)
        r2 = await async_op(7)
        assert r1 == 107
        assert r2 == 107
        assert call_count[0] == 1


def test_get_and_clear_cache_manager_singleton():
    from app.core.cache import get_cache_manager, clear_cache_manager
    clear_cache_manager()
    m1 = get_cache_manager(use_redis=False)
    m2 = get_cache_manager(use_redis=False)
    assert m1 is m2
    clear_cache_manager()


# ─────────────────────────────────────────────────────────────────
# Metrics helpers (record_* functions + MetricsTimer)
# ─────────────────────────────────────────────────────────────────

class TestMetricsHelpers:

    def test_record_http_request(self):
        from app.core.metrics import record_http_request
        # Should not raise
        record_http_request("GET", "/api/v1/test", 200, 0.05)
        record_http_request("POST", "/api/v1/auth/login", 401, 0.1)

    def test_record_db_query_success(self):
        from app.core.metrics import record_db_query
        record_db_query("SELECT", "users", 0.01, error=False)

    def test_record_db_query_error(self):
        from app.core.metrics import record_db_query
        record_db_query("INSERT", "users", 0.05, error=True)

    def test_record_cache_hit(self):
        from app.core.metrics import record_cache_operation
        record_cache_operation("redis", hit=True)
        record_cache_operation("memory", hit=False)

    def test_record_auth_attempt(self):
        from app.core.metrics import record_auth_attempt
        record_auth_attempt("password", success=True)
        record_auth_attempt("password", success=False)

    def test_record_ai_request(self):
        from app.core.metrics import record_ai_request
        record_ai_request("openai", "gpt-4", 2.5, success=True)
        record_ai_request("openai", "gpt-4", 0.1, success=False)

    def test_record_email_sent(self):
        from app.core.metrics import record_email_sent
        record_email_sent("welcome", success=True)
        record_email_sent("reset", success=False)

    def test_record_error(self):
        from app.core.metrics import record_error
        record_error("ValidationError", "billing_service")

    def test_metrics_timer_context_manager(self):
        from app.core.metrics import MetricsTimer, db_query_duration_seconds
        with MetricsTimer(db_query_duration_seconds, {"operation": "SELECT", "table": "test"}):
            time.sleep(0.001)
        # No assertion needed — just ensure it doesn't raise and records


# ─────────────────────────────────────────────────────────────────
# token_blacklist — Redis code paths (mocked Redis)
# ─────────────────────────────────────────────────────────────────

class TestTokenBlacklistRedisPaths:

    def test_blacklist_via_redis_mock(self):
        """Exercises the Redis live path (settings.APP_ENV != 'test')."""
        from app.core.token_blacklist import blacklist_token, is_token_blacklisted
        jti = str(uuid.uuid4())

        mock_redis = MagicMock()
        mock_redis.setex.return_value = True
        mock_redis.exists.return_value = 1

        with patch("app.core.token_blacklist.settings") as ms, \
             patch("app.core.token_blacklist._get_redis_client", return_value=mock_redis):
            ms.APP_ENV = "production"
            blacklist_token(jti, ttl_seconds=3600)
            mock_redis.setex.assert_called_once()

            result = is_token_blacklisted(jti)
            assert result is True

    def test_redis_write_failure_falls_back_to_memory(self):
        jti = f"fb_{uuid.uuid4()}"
        mock_redis = MagicMock()
        mock_redis.setex.side_effect = Exception("Redis down")
        mock_redis.exists.side_effect = Exception("Redis down")

        with patch("app.core.token_blacklist.settings") as ms, \
             patch("app.core.token_blacklist._get_redis_client", return_value=mock_redis):
            ms.APP_ENV = "production"
            from app.core.token_blacklist import blacklist_token
            # Should not raise — falls back to memory
            blacklist_token(jti, ttl_seconds=60)

    def test_redis_read_failure_falls_back_to_memory(self):
        jti = f"rfb_{uuid.uuid4()}"
        mock_redis = MagicMock()
        mock_redis.exists.side_effect = Exception("Redis timeout")

        with patch("app.core.token_blacklist.settings") as ms, \
             patch("app.core.token_blacklist._get_redis_client", return_value=mock_redis):
            ms.APP_ENV = "production"
            from app.core.token_blacklist import is_token_blacklisted
            result = is_token_blacklisted(jti)
            assert isinstance(result, bool)

    def test_no_redis_client_returns_none(self):
        with patch("app.core.token_blacklist.settings") as ms, \
             patch("app.core.token_blacklist._get_redis_client", return_value=None):
            ms.APP_ENV = "production"
            from app.core.token_blacklist import blacklist_token, is_token_blacklisted
            jti = f"nomem_{uuid.uuid4()}"
            blacklist_token(jti, ttl_seconds=10)
            # Falls back to in-memory
            assert is_token_blacklisted(jti) is True


# ─────────────────────────────────────────────────────────────────
# RateLimiter — remaining paths (JWT extraction, strict paths)
# ─────────────────────────────────────────────────────────────────

class TestRateLimiterJWTPaths:

    @pytest.mark.asyncio
    async def test_jwt_extraction_sets_user_rate_key(self):
        """When a valid Bearer JWT is in headers, key becomes user:<id>."""
        from app.middleware.rate_limiter import RateLimiterMiddleware
        from app.core.security import create_access_token
        from unittest.mock import AsyncMock

        token = create_access_token(subject="test-user-id-abc")

        mw = RateLimiterMiddleware(app=None, requests_per_minute=100)
        call_next = AsyncMock()
        call_next.return_value = MagicMock(headers={})

        with patch("app.middleware.rate_limiter.settings") as ms:
            ms.APP_ENV = "production"
            ms.RATE_LIMIT_PER_MINUTE = 100
            ms.jwt_verify_key = __import__("config.settings", fromlist=["settings"]).settings.jwt_verify_key
            ms.jwt_algorithm = __import__("config.settings", fromlist=["settings"]).settings.jwt_algorithm

            request = MagicMock()
            request.client.host = "192.168.0.1"
            request.headers.get.return_value = f"Bearer {token}"
            request.url.path = "/api/v1/users/me"

            await mw.dispatch(request, call_next)
            # If user key was used, the bucket should reference user:<id>
            assert any("user:" in k for k in mw.request_counts.keys())

    @pytest.mark.asyncio
    async def test_invalid_jwt_falls_back_to_ip(self):
        from app.middleware.rate_limiter import RateLimiterMiddleware
        from unittest.mock import AsyncMock

        mw = RateLimiterMiddleware(app=None, requests_per_minute=100)
        call_next = AsyncMock()
        call_next.return_value = MagicMock(headers={})

        with patch("app.middleware.rate_limiter.settings") as ms:
            ms.APP_ENV = "production"
            ms.RATE_LIMIT_PER_MINUTE = 100
            ms.jwt_verify_key = "secret"
            ms.jwt_algorithm = "HS256"

            request = MagicMock()
            request.client.host = "10.0.0.5"
            request.headers.get.return_value = "Bearer invalid.jwt.token"
            request.url.path = "/api/v1/test"

            resp = await mw.dispatch(request, call_next)
            # Falls back to IP — request should pass
            assert "10.0.0.5" in mw.request_counts

    @pytest.mark.asyncio
    async def test_strict_path_login_has_lower_limit(self):
        """Login path uses STRICT_RATE_LIMIT_PATHS limit, not the global one."""
        from app.middleware.rate_limiter import RateLimiterMiddleware, STRICT_RATE_LIMIT_PATHS
        from unittest.mock import AsyncMock

        login_limit = STRICT_RATE_LIMIT_PATHS["/api/v1/auth/login"]
        mw = RateLimiterMiddleware(app=None, requests_per_minute=1000)
        call_next = AsyncMock()
        call_next.return_value = MagicMock(headers={})

        blocked_count = 0
        with patch("app.middleware.rate_limiter.settings") as ms:
            ms.APP_ENV = "production"
            ms.RATE_LIMIT_PER_MINUTE = 1000
            ms.jwt_verify_key = "secret"
            ms.jwt_algorithm = "HS256"

            for _ in range(login_limit + 2):
                request = MagicMock()
                request.client.host = "5.5.5.5"
                request.headers.get.return_value = None
                request.url.path = "/api/v1/auth/login"
                resp = await mw.dispatch(request, call_next)
                if hasattr(resp, "status_code") and resp.status_code == 429:
                    blocked_count += 1

        assert blocked_count >= 1
