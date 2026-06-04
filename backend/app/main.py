from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.models.models import UPIShieldEvent, Case, ThreatFeedAlert  # Ensure models are imported for metadata registration
from app.routers import health, documents, fraud_dna, phishing, dashboard, ai, upi, cases, threats, fusion, research, export

# Automatic database initialization
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    export.router
):
    app.include_router(router)



@app.get("/")
def root():
    return {"message": f"{settings.APP_NAME} backend running", "version": settings.APP_VERSION}