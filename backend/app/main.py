from __future__ import annotations

import logging
import os
import re
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.config import settings
from app.database import engine, Base
from app.dependencies.auth import DEV_MODE_HEADER, is_dev_mode
from app.lifespan import lifespan
from app.models.models import UPIShieldEvent, Case, ThreatFeedAlert  # for metadata
from app.rate_limit import limiter
from app.routers import (
    ai,
    cases,
    dashboard,
    documents,
    export,
    fraud_dna,
    fusion,
    health,
    metrics,
    phishing,
    research,
    stream_router,
    threats,
    upi,
)
from app.routers.probes import router as probes_router

logger = logging.getLogger("lumint.main")


# ─────────────────────────────────────────────────────────────────────
# Request ID middleware
# ─────────────────────────────────────────────────────────────────────


class RequestIDMiddleware:
    """Attach a stable request id to every HTTP response and request scope.

    Honours an inbound ``X-Request-ID`` (so a frontend or upstream proxy
    can correlate) and otherwise generates a fresh UUID4. The id is
    echoed back as ``X-Request-ID`` and exposed via
    ``request.state.request_id`` for downstream handlers.

    Implemented as a pure ASGI middleware (NOT ``BaseHTTPMiddleware``)
    because ``BaseHTTPMiddleware`` cannot pass through WebSocket scopes —
    it raises a denial on the WebSocket handshake and breaks our
    ``/ws/threats`` stream.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            # WebSocket, lifespan — pass through unchanged.
            await self.app(scope, receive, send)
            return

        # Read X-Request-ID from the incoming headers.
        headers = scope.get("headers", []) or []
        rid: Optional[str] = None
        for k, v in headers:
            if k == b"x-request-id":
                try:
                    rid = v.decode("latin-1")
                except Exception:
                    rid = None
                break

        if not rid or len(rid) > 256 or not _SAFE_REQUEST_ID.match(rid):
            rid = str(uuid.uuid4())

        # Stash for the request handler.
        scope.setdefault("state", {})
        # Starlette puts request.state on the Request object, not in the
        # ASGI scope. The simplest portable way is to set a sentinel
        # we can read back from the request handler.
        scope["_lumint_request_id"] = rid

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                hdrs = list(message.get("headers", []))
                hdrs.append((b"x-request-id", rid.encode("latin-1")))
                message["headers"] = hdrs
            await send(message)

        await self.app(scope, receive, send_wrapper)


# Anything that would break log aggregation / header smuggling goes here.
_SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._\-:]{1,256}$")


# ─────────────────────────────────────────────────────────────────────
# Security headers middleware (HSTS, CSP, Permissions, etc.)
# ─────────────────────────────────────────────────────────────────────


class SecurityHeadersMiddleware:
    """Apply a strict set of response headers to every HTTP response.

    The set is the OWASP Secure Headers Project baseline plus a
    Content-Security-Policy tuned for our JSON-only API surface.

    Implemented as a pure ASGI middleware to support WebSocket connections.
    """

    # Our API is JSON-only — the CSP can be very strict. We allow:
    #  - 'self' for any same-origin resources (none expected for an API)
    #  - inline JSON responses (CSP doesn't apply to JSON, but it's set
    #    so browsers will not interpret a misconfigured MIME as HTML)
    CSP = (
        "default-src 'none'; "
        "frame-ancestors 'none'; "
        "form-action 'none'; "
        "base-uri 'none'; "
        "img-src 'none'; "
        "media-src 'none'; "
        "object-src 'none'; "
        "script-src 'none'; "
        "style-src 'none'; "
        "connect-src 'self'"
    )

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            # WebSocket, lifespan — pass through unchanged.
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                hdrs = list(message.get("headers", []))

                # Block MIME sniffing (drive-by image-as-html XSS).
                hdrs.append((b"x-content-type-options", b"nosniff"))
                # Don't allow iframe embedding.
                hdrs.append((b"x-frame-options", b"DENY"))
                # Tight referrer policy.
                hdrs.append((b"referrer-policy", b"no-referrer"))
                # Disable powerful features we don't use.
                hdrs.append((b"permissions-policy", (
                    b"geolocation=(), microphone=(), camera=(), payment=(), "
                    b"usb=(), magnetometer=(), gyroscope=(), accelerometer=()"
                )))
                # Cross-origin isolation hints.
                hdrs.append((b"cross-origin-opener-policy", b"same-origin"))
                hdrs.append((b"cross-origin-resource-policy", b"same-origin"))
                # Strict CSP for the (JSON-only) API.
                hdrs.append((b"content-security-policy", self.CSP.encode("latin-1")))

                # HSTS only on HTTPS — sending HSTS on HTTP has no effect.
                if scope.get("scheme") == "https":
                    hdrs.append((b"strict-transport-security",
                               b"max-age=63072000; includeSubDomains; preload"))

                # Make the dev-mode state visible to the operator — but
                # NEVER leak it in production. An attacker scanning
                # ``X-Lumint-Dev-Mode: true`` would instantly know the
                # auth bypass is active and start hammering the API.
                if is_dev_mode() and os.environ.get("APP_ENV", "development").strip().lower() in {"development", "dev", "test"}:
                    hdrs.append((DEV_MODE_HEADER.encode("latin-1"), b"true"))

                message["headers"] = hdrs

            await send(message)

        await self.app(scope, receive, send_wrapper)


# ─────────────────────────────────────────────────────────────────────
# Body-size guard ASGI middleware (defense-in-depth on top of the
# per-endpoint MAX_UPLOAD_* caps).
# ─────────────────────────────────────────────────────────────────────


class BodySizeLimitMiddleware:
    """ASGI middleware that rejects any request whose Content-Length
    exceeds the configured cap.

    Many of our endpoints already read the body in a streaming
    `UploadFile = File(...)` way and check size after read. This
    middleware provides a *fast* pre-check using the Content-Length
    header so a hostile client cannot stream an unbounded body before
    our handler decides to reject it.

    We also defend against Content-Length lying (chunked transfer
    encoding, no Content-Length) by counting bytes as they arrive.
    """

    def __init__(
        self,
        app: ASGIApp,
        max_body_bytes: int = 20 * 1024 * 1024,  # 20MB global cap
    ) -> None:
        self.app = app
        self.max = max_body_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # 1) Trust Content-Length as a fast path.
        cl = next(
            (v for k, v in scope.get("headers", []) if k == b"content-length"),
            None,
        )
        if cl is not None:
            try:
                cl_int = int(cl)
            except ValueError:
                cl_int = -1
            if cl_int > self.max:
                await _reject_too_large(send, self.max)
                return

        # 2) For chunked / no-Content-Length bodies, count bytes as
        # they arrive. When the running total crosses the cap, emit
        # 413 from inside the receive callback (so the response is
        # committed before the app sees a disconnect) and return
        # `http.disconnect` to short-circuit the app.
        #
        # Why emit 413 *before* the disconnect: Starlette's exception
        # handler checks whether `http.response.start` has already
        # been sent before converting a `ClientDisconnect` into a 500.
        # Because `_reject_too_large` calls `send({...start...})` and
        # `send({...body...})` first, the response is committed and
        # the disconnect is logged as a benign `ClientDisconnect` —
        # never as a 500.
        total = 0
        overflowed = False
        buffered_first: dict | None = None

        async def counting_receive() -> dict:
            nonlocal total, overflowed, buffered_first
            if buffered_first is not None:
                msg = buffered_first
                buffered_first = None
                return msg
            msg = await receive()
            if msg["type"] == "http.request":
                body = msg.get("body", b"") or b""
                total += len(body)
                if total > self.max and not overflowed:
                    overflowed = True
                    scope.setdefault("state", {})["body_overflow"] = True
                    # Commit 413 BEFORE returning disconnect, so the
                    # app's response handler doesn't try to send a
                    # competing 500 over the wire.
                    await _reject_too_large(send, self.max)
                    return {"type": "http.disconnect"}
            return msg

        # Peek the first chunk — if it alone exceeds the cap, emit
        # 413 race-free without ever entering the app.
        peek = await receive()
        if peek["type"] == "http.request":
            peek_body = peek.get("body", b"") or b""
            total += len(peek_body)
            if total > self.max:
                scope.setdefault("state", {})["body_overflow"] = True
                await _reject_too_large(send, self.max)
                # Drain remaining body so the socket can be released.
                while peek.get("more_body", False):
                    peek = await receive()
                    if peek["type"] != "http.request":
                        break
                return
            # First chunk fits — buffer it for the app and let it
            # continue reading via counting_receive.
            buffered_first = peek

        await self.app(scope, counting_receive, send)


async def _reject_too_large(send, max_bytes: int) -> None:
    body = (
        b'{"detail":"Request body too large. '
        b'Maximum allowed is ' + str(max_bytes).encode() + b' bytes."}'
    )
    await send(
        {
            "type": "http.response.start",
            "status": 413,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode()),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})


# ─────────────────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────────────────


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)
app.state.limiter = limiter

# ─────────────────────────────────────────────────────────────────────
# Wildcard-aware CORS origin check
# ─────────────────────────────────────────────────────────────────────

_WILDCARD_RE = re.compile(r"^https?://([^*]+\.[*])[^/]*$")
_EXACT_RE = re.compile(r"^https?://[^*]+$")


def _cors_origin_allowed(origin: str, allowed: list[str]) -> bool:
    """Return True if *origin* is allowed by *allowed* list.

    Supports exact host match and simple suffix wildcard
    ``https://*.vercel.app`` patterns.
    """
    if not origin:
        return False
    for entry in (o.strip() for o in allowed if o.strip()):
        if entry == "*":
            return True
        if entry.startswith("http://") or entry.startswith("https://"):
            # Exact match against scheme+host
            if origin == entry:
                return True
            # Suffix wildcard like https://*.vercel.app
            if "*" in entry:
                # Escape everything except the * then replace * with .*
                regex = "^" + re.escape(entry).replace(r"\*", ".*") + "$"
                if re.match(regex, origin):
                    return True
            continue
        # Plain host entry — match as a suffix
        if origin.endswith("/" + entry) or origin.endswith("://" + entry):
            return True
    return False


class WildcardCorsMiddleware(BaseHTTPMiddleware):
    """Reject CORS origins not present in ``settings.origins_list``.

    The allowlist supports exact origins and explicit wildcard entries such as
    ``https://*.vercel.app``. It intentionally does not trust every Vercel
    preview URL by default; any preview wildcard must be configured in the
    deployment environment.
    """

    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin", "")
        allowed_origins = list(settings.origins_list)

        if origin:
            origin_ok = _cors_origin_allowed(origin, allowed_origins)
        else:
            # No Origin header → not a CORS request (e.g. tests, curl,
            # server-to-server via the Next.js proxy). These are always
            # safe to allow — CORS only protects browser-initiated
            # cross-origin XHR, not same-origin or non-browser traffic.
            origin_ok = True

        if not origin_ok:
            if request.method == "OPTIONS":
                return JSONResponse(
                    {"detail": "Disallowed CORS origin"},
                    status_code=400,
                )
            return JSONResponse(
                {"detail": "Disallowed CORS origin"},
                status_code=400,
            )

        # Let the request through. For OPTIONS, short-circuit now so we
        # can emit our own CORS headers.
        if request.method == "OPTIONS":
            return JSONResponse(
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "Accept, Accept-Language, Authorization, Content-Language, Content-Type, X-Api-Key, X-Request-ID",
                    "Access-Control-Max-Age": "3600",
                },
            )

        response = await call_next(request)

        # Inject CORS headers so the browser accepts the response even
        # if the downstream CORSMiddleware doesn't reflect this origin.
        if origin:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"

        return response


# ── Middleware order (outermost first)
# BodySizeLimit is OUTERMOST — it sees the raw body before anything else.
app.add_middleware(BodySizeLimitMiddleware, max_body_bytes=20 * 1024 * 1024)
# Then security headers, then request id, then rate limit, then wildcard CORS, then standard CORS.
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(WildcardCorsMiddleware)
# ProxyHeaders rewrites scheme/host from X-Forwarded-* so the
# SecurityHeadersMiddleware sees `scope["scheme"] == "https"` behind
# Render/Vercel/Nginx and can attach HSTS. Trust only the loopback /
# private hops we expect (override with TRUSTED_PROXIES env if your
# edge runs elsewhere).
app.add_middleware(
    ProxyHeadersMiddleware,
    trusted_hosts=os.environ.get("TRUSTED_PROXIES", "127.0.0.1,::1").split(","),
)
# CORS — origins are env-driven (see app.config.origins_list).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Api-Key", "X-Request-ID"],
    # We never let the response leak beyond an hour.
    max_age=3600,
)


# ─────────────────────────────────────────────────────────────────────
# Global exception handlers — never leak stack traces or internal paths.
# ─────────────────────────────────────────────────────────────────────


@app.exception_handler(Exception)
async def _safe_exception_handler(request: Request, exc: Exception):  # noqa: ARG001
    rid = (
        getattr(request.state, "request_id", None)
        or request.scope.get("_lumint_request_id")
    )
    # Log full exception server-side (with request id for correlation).
    logger.exception("Unhandled error [request_id=%s]", rid)
    # Return a generic error to the client. The request id lets the
    # operator correlate without exposing internals.
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error.",
            "request_id": rid,
        },
    )


# ─────────────────────────────────────────────────────────────────────
# Routers
# ─────────────────────────────────────────────────────────────────────

for router in (
    health.router,
    documents.router,
    fraud_dna.router,
    phishing.router,
    dashboard.router,
    ai.router,
    upi.router,
    cases.router,
    threats.router,
    fusion.router,
    research.router,
    export.router,
    stream_router.router,
    metrics.router,
):
    app.include_router(router)

# Liveness + readiness probes at root (no /api prefix).
app.include_router(probes_router)


@app.get("/")
def root():
    return {
        "message": f"{settings.APP_NAME} backend running",
        "version": settings.APP_VERSION,
    }


# ── Aliases for `/health` and `/ready` so the frontend `useApiHealth`
# ── hook (which polls `/health`) and Render's health-check path work
# ── without changing the existing k8s-style `/healthz` + `/readyz` routes.
@app.get("/health", include_in_schema=False)
def health_alias():
    from app.routers.probes import healthz  # local import avoids circulars
    return healthz()


@app.get("/ready", include_in_schema=False)
def ready_alias():
    from app.routers.probes import readyz
    return readyz()
