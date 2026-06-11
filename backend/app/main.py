from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.models.models import UPIShieldEvent, Case, ThreatFeedAlert  # Ensure models are imported for metadata registration
from app.lifespan import lifespan
from app.routers import health, documents, fraud_dna, phishing, dashboard, ai, upi, cases, threats, fusion, research, export, stream_router
from app.routers.probes import router as probes_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

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