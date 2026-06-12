"""Simple in-memory TTL cache for expensive operations.

Caching is intentionally opt-in: each router decides whether its
endpoint is safe to cache (deterministic on file contents, side-effect
free). The cache key is typically a SHA-256 of the request payload so
identical uploads hit the cache.

Notes on the design:

* **In-process, not distributed.** Render instances each have their
  own cache. This is fine for a quick win — the goal is to avoid
  re-analyzing the same screenshot within a 10-minute window, not to
  coordinate between replicas. If/when we move to Redis, the public
  API (get/set/hash_file) stays the same.
* **TTL with size cap.** Old entries expire on read. When the cache
  is full, the *oldest* entry is evicted. We use a tiny linear scan
  for eviction; with max_size=500 it's a non-issue.
* **No locking.** Python's GIL makes ``get``/``set`` atomic for our
  purposes. We don't need ``asyncio.Lock`` for a simple ``dict``.
"""
from __future__ import annotations

import hashlib
import logging
import time
from functools import wraps
from typing import Any, Callable, Optional

logger = logging.getLogger("lumint.core.cache")


class TTLCache:
    """Time-based cache with TTL expiration and bounded size."""

    def __init__(self, ttl_seconds: int = 300, max_size: int = 1000) -> None:
        self.ttl = ttl_seconds
        self.max_size = max_size
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        """Return the cached value, or None if missing or expired."""
        entry = self._store.get(key)
        if entry is None:
            return None
        ts, value = entry
        if time.time() - ts > self.ttl:
            # Expired — clean up and miss
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        """Insert a value, evicting the oldest entry if at capacity."""
        if len(self._store) >= self.max_size:
            oldest_key = min(self._store, key=lambda k: self._store[k][0])
            self._store.pop(oldest_key, None)
        self._store[key] = (time.time(), value)

    def clear(self) -> None:
        """Drop all entries. Useful in tests."""
        self._store.clear()

    def stats(self) -> dict[str, int]:
        """Return cache size and capacity for /api/metrics/cache."""
        return {
            "size": len(self._store),
            "max_size": self.max_size,
        }


# Global caches (singleton pattern)
upi_cache = TTLCache(ttl_seconds=600, max_size=500)  # 10 min TTL
phish_cache = TTLCache(ttl_seconds=300, max_size=1000)  # 5 min TTL


def cache_result(
    cache: TTLCache,
    key_fn: Callable[..., str],
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to cache function results.

    ``key_fn(*args, **kwargs)`` must return a stable string key. The
    wrapped function is only called on a cache miss.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = key_fn(*args, **kwargs)
            cached = cache.get(key)
            if cached is not None:
                logger.debug("Cache hit for key=%s", key[:16])
                return cached
            result = func(*args, **kwargs)
            cache.set(key, result)
            return result

        return wrapper

    return decorator


def hash_file(file_bytes: bytes) -> str:
    """SHA-256 hash of file content for use as a cache key."""
    return hashlib.sha256(file_bytes).hexdigest()


def hash_payload(payload: Any) -> str:
    """Stable hash of a JSON-serialisable payload.

    Used to cache URL-risk results by their canonical URL string.
    ``sort_keys=True`` ensures ``{"a": 1, "b": 2}`` and ``{"b": 2, "a":
    1}`` hash identically.
    """
    import json

    canonical = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
