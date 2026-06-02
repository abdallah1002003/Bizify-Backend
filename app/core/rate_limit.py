"""
Application rate limiter.

Wraps slowapi so auth/OTP/password-reset endpoints can be throttled to stop
brute-force (password & OTP) and email-bombing abuse. The limiter is disabled
automatically under pytest so the test suite's repeated logins don't trip it.
"""
import sys

from slowapi import Limiter
from slowapi.util import get_remote_address

# Disable limits while running tests (same convention used in app.core.config).
_TESTING = "pytest" in sys.modules

limiter = Limiter(key_func=get_remote_address, enabled=not _TESTING)
