from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
from app.config import settings
from app.database import engine, Base
from app.models.models import UPIShieldEvent, Case, ThreatFeedAlert  # Ensure models are imported for metadata registration
from app.lifespan import lifespan
from app.routers import health, documents, fraud_dna, phishing, dashboard, ai, upi, cases, threats, fusion, research, export, stream_router
from app.routers.probes import router as probes_router


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a stable request id to every response and the request scope.

    Honours an inbound ``X-Request-ID`` header (so a frontend or upstream
    proxy can correlate) and otherwise generates a fresh UUID4. The id is
    echoed back on the response as ``X-Request-ID`` and is also available
    to downstream handlers via ``request.state.request_id``.
    """

    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(RequestIDMiddleware)

# Security headers — applied to every response
@app.middleware("http")
async def add_security_headers(request, call_next):
    """Add baseline security headers to every HTTP response.

    - X-Content-Type-Options: stops MIME-sniffing attacks
    - X-Frame-Options: stops clickjacking by refusing iframe embedding
    - Referrer-Policy: only send the origin on cross-origin requests
    - Permissions-Policy: deny unused powerful features (geolocation, mic, camera)
    - Strict-Transport-Security: only on HTTPS — tells browsers to upgrade
      all subsequent requests to HTTPS for one year
    """
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

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
    stream_router.router
):
    app.include_router(router)

# Liveness + readiness probes at root (no /api prefix).
app.include_router(probes_router)



@app.get("/")
def root():
    return {"message": f"{settings.APP_NAME} backend running", "version": settings.APP_VERSION}