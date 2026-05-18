"""
app/core/limiter.py
===================
Shared slowapi rate-limiter instance.

Import `limiter` wherever you need @limiter.limit() decorators.
The limiter is registered on the FastAPI app in main.py.

Rate limits use the request IP as the key (default). For authenticated
endpoints the IP is the correct key — per-user limits are already handled
by the AI usage counter in check_ai_usage.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
