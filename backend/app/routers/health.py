from fastapi import APIRouter
from app.config import settings
from app.database import check_db_connection

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health_check():
    db_ok = check_db_connection()
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": "connected" if db_ok else "unavailable",
    }