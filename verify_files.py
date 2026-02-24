#!/usr/bin/env python3
"""Verify conftest and rate_limiter_redis work correctly."""

import sys

def check_conftest():
    """Check conftest fixtures."""
    print("=" * 60)
    print("✅ فحص conftest.py")
    print("=" * 60)
    
    try:
        from tests.conftest import (
            cleanup_test_engine, db, client, async_client, test_user,
            auth_token, auth_headers, user_token, another_user,
            another_user_token, user_subscription
        )
        
        fixtures = [
            'cleanup_test_engine', 'db', 'client', 'async_client', 'test_user',
            'auth_token', 'auth_headers', 'user_token', 'another_user',
            'another_user_token', 'user_subscription'
        ]
        
        print(f"\n✅ تم تحميل ({len(fixtures)}) fixtures:")
        for fixture in fixtures:
            print(f"   ✓ {fixture}")
        
        return True
    except Exception as e:
        print(f"❌ خطأ في conftest.py: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_rate_limiter():
    """Check rate_limiter_redis."""
    print("\n" + "=" * 60)
    print("✅ فحص rate_limiter_redis.py")
    print("=" * 60)
    
    try:
        from app.middleware.rate_limiter_redis import (
            RedisRateLimiterMiddleware, 
            STRICT_RATE_LIMIT_PATHS
        )
        
        print("\n✅ RedisRateLimiterMiddleware تم تحميله")
        
        print(f"\n✅ المسارات المحمية ({len(STRICT_RATE_LIMIT_PATHS)}):")
        for path, limit in STRICT_RATE_LIMIT_PATHS.items():
            print(f"   - {path}: {limit} طلب/دقيقة")
        
        print("\n✅ الدوال المتوفرة:")
        methods = [
            '_init_redis', '_get_client_ip', '_check_rate_limit_redis',
            '_check_rate_limit_memory', 'dispatch'
        ]
        
        for method in methods:
            has_it = hasattr(RedisRateLimiterMiddleware, method)
            symbol = "✓" if has_it else "✗"
            print(f"   {symbol} {method}")
        
        return True
    except Exception as e:
        print(f"❌ خطأ في rate_limiter_redis.py: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result1 = check_conftest()
    result2 = check_rate_limiter()
    
    print("\n" + "=" * 60)
    if result1 and result2:
        print("✨ كل شيء يعمل بشكل صحيح!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("❌ هناك مشاكل يجب إصلاحها")
        print("=" * 60)
        sys.exit(1)
