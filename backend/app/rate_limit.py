"""Shared rate-limiter instance used across the application.

Defined in its own module so routers can import it without triggering a
circular import on ``app.main``. The limiter is keyed by remote address
(IP) by default, with a 200/minute fallback cap applied globally.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
