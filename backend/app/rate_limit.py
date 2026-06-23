"""Shared rate-limiter instance used across the application.

Defined in its own module so routers can import it without triggering a
circular import on ``app.main``.

Partitioning strategy
---------------------
The default ``get_remote_address`` key_func partitions the budget by client
IP, which is wrong for an API-key-authenticated service: two distinct API
keys behind the same NAT (corporate proxy, mobile carrier, shared
egress) would share one 30/minute budget.

We define :func:`api_key_or_ip_key` which partitions the rate-limit
bucket by:

    1. ``X-Api-Key`` header if present (canonical, preferred).
    2. ``Authorization: Bearer <key>`` header (legacy) — we hash the
       *token* (not the prefix) so two different bearer tokens behind the
       same NAT still get distinct buckets.
    3. Remote address as a fallback.

We use a SHA-256 prefix of the raw token rather than the token itself so
that:
    - Bucket keys never contain the plaintext credential (a leaked log
      line or metrics scrape can't recover the API key).
    - All bucket keys have a fixed, bounded length (17 chars), so the
      slowapi/moving-window storage stays compact.

Per-endpoint declarations (``@limiter.limit("30/minute", key_func=...)``)
override the limiter-wide default so the API-key partition is what
actually counts toward the budget — the IP fallback only kicks in when
no credential was supplied (e.g. unauthenticated probes in dev mode,
which are still rate-limited by IP).
"""
import hashlib

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def _hash_token(token: str) -> str:
    """Return a short, non-reversible identifier for an API key.

    We hash with SHA-256 and keep the first 16 hex chars (64 bits of
    entropy). That is more than enough to avoid collisions in any
    realistic rate-limit window and never lets a reader reconstruct the
    raw key from a log line or metrics dump.
    """
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return digest[:16]


def api_key_or_ip_key(request: Request) -> str:
    """Return the partition key for rate-limit bucketing.

    Order of preference:

    1. ``X-Api-Key`` header — the canonical API key. We partition by the
       first 4 characters (the public prefix that ``AuthResult`` already
       exposes) plus a hash of the full token. Using the prefix keeps
       log lines compact while the hash prevents two distinct keys that
       share a prefix from colliding.
    2. ``Authorization: Bearer <key>`` — legacy clients. We accept the
       scheme and partition by a hash of the raw bearer token.
    3. ``request.client.host`` (slowapi's ``get_remote_address``).

    The returned string is always prefixed with ``apikey:`` or ``ip:``
    so an operator reading slowapi storage can't confuse a key-derived
    bucket with an IP-derived one.
    """
    # Canonical: X-Api-Key
    x_api_key = request.headers.get("x-api-key")
    if x_api_key:
        prefix = x_api_key[:4] if len(x_api_key) >= 4 else x_api_key
        return f"apikey:{prefix}:{_hash_token(x_api_key)}"

    # Legacy: Authorization: Bearer <key>
    authorization = request.headers.get("authorization")
    if authorization:
        token: str | None
        if authorization.lower().startswith("bearer "):
            token = authorization[7:].strip()
        else:
            # Tolerate raw `<key>` without the scheme (some old clients).
            token = authorization.strip()
        if token:
            return f"apikey:bearer:{_hash_token(token)}"

    # Fallback: IP. Prefix distinguishes this from API-key buckets in
    # any operator-facing log.
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(key_func=api_key_or_ip_key, default_limits=["200/minute"])