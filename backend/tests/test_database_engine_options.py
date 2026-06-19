"""Regression tests for backend/app/database.py engine options.

Ensures non-SQLite URLs (e.g. Postgres) get `pool_recycle=300` so that
stale connections behind proxies/firewalls are recycled every 5 minutes.
SQLite URLs must NOT set pool_recycle (it is ignored anyway and could
cause confusion).
"""
from app.database import _engine_options


def test_postgres_url_sets_pool_recycle_300():
    """A Postgres URL must include pool_recycle=300 in engine options."""
    options = _engine_options("postgresql+psycopg://user:pass@localhost:5432/dbname")
    assert options.get("pool_recycle") == 300


def test_postgres_url_keeps_existing_options():
    """Adding pool_recycle must not clobber other engine options."""
    options = _engine_options("postgresql+psycopg://user:pass@localhost:5432/dbname")
    assert options.get("pool_pre_ping") is True


def test_sqlite_url_does_not_set_pool_recycle():
    """SQLite must not have pool_recycle set (it is ignored and unnecessary)."""
    options = _engine_options("sqlite:///./test.db")
    assert "pool_recycle" not in options
