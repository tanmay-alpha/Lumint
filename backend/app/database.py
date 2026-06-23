from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings


def _engine_options(database_url: str) -> dict[str, Any]:
    options: dict[str, Any] = {
        "pool_pre_ping": True,
        "echo": settings.DEBUG,
    }
    url = make_url(database_url)

    if url.drivername.startswith("sqlite"):
        options["connect_args"] = {
            "check_same_thread": False,
            "timeout": 30
        }
        if url.database in (None, "", ":memory:"):
            options["poolclass"] = StaticPool
    else:
        # Recycle connections every 5 minutes to avoid stale connections behind proxies/firewalls
        options["pool_recycle"] = 300

    return options


engine = create_engine(
    settings.DATABASE_URL,
    **_engine_options(settings.DATABASE_URL),
)

from sqlalchemy import event

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    url = make_url(settings.DATABASE_URL)
    if url.drivername.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
