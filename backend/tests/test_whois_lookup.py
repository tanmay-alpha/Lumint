import asyncio
import sys
from datetime import datetime, timedelta, timezone

import pytest

from app.services.phishshield.whois_lookup import _sync_whois, lookup_whois


class FakeWhoisResult:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class FakeWhoisModule:
    """Stand-in for the `whois` module with a configurable `whois()` fn."""

    def __init__(self, fn):
        self._fn = fn

    def whois(self, domain):
        return self._fn(domain)


def _install_fake_whois(monkeypatch, fn):
    """Inject a fake `whois` module into sys.modules so the lazy import picks it up."""
    fake = FakeWhoisModule(fn)
    monkeypatch.setitem(sys.modules, "whois", fake)
    return fake


def test_whois_recently_registered(monkeypatch):
    recent = datetime.now(timezone.utc) - timedelta(days=10)
    expiration = datetime.now(timezone.utc) + timedelta(days=365)
    fake = FakeWhoisResult(
        registrar="TestRegistrar",
        creation_date=recent,
        expiration_date=expiration,
        country="US",
    )
    _install_fake_whois(monkeypatch, lambda d: fake)
    result = _sync_whois("example.com")
    assert result is not None
    assert result["age_days"] == 10
    assert result["is_recently_registered"] is True
    assert result["registrar"] == "TestRegistrar"
    assert result["country"] == "US"


def test_whois_old_domain(monkeypatch):
    old = datetime.now(timezone.utc) - timedelta(days=2000)
    expiration = datetime.now(timezone.utc) + timedelta(days=365)
    fake = FakeWhoisResult(
        registrar="TestRegistrar",
        creation_date=old,
        expiration_date=expiration,
        country="US",
    )
    _install_fake_whois(monkeypatch, lambda d: fake)
    result = _sync_whois("example.com")
    assert result is not None
    assert result["is_recently_registered"] is False
    assert result["age_days"] == 2000


def test_whois_exception_returns_none(monkeypatch):
    def boom(domain):
        raise Exception("network error")

    _install_fake_whois(monkeypatch, boom)
    assert _sync_whois("example.com") is None


def test_whois_no_creation_date_returns_none(monkeypatch):
    fake = FakeWhoisResult(registrar="X", creation_date=None, country="US")
    _install_fake_whois(monkeypatch, lambda d: fake)
    assert _sync_whois("example.com") is None


def test_whois_naive_datetime_assumes_utc(monkeypatch):
    """WHOIS responses sometimes come back without tzinfo; we coerce to UTC."""
    naive = (datetime.now(timezone.utc) - timedelta(days=100)).replace(tzinfo=None)
    fake = FakeWhoisResult(
        registrar="X",
        creation_date=naive,
        expiration_date=None,
        country=None,
    )
    _install_fake_whois(monkeypatch, lambda d: fake)
    result = _sync_whois("example.com")
    assert result is not None
    assert 99 <= result["age_days"] <= 101
    assert result["is_recently_registered"] is False


def test_whois_creation_date_list_picks_first(monkeypatch):
    """Some registrars return creation_date as a list of datetimes."""
    real_creation = datetime.now(timezone.utc) - timedelta(days=50)
    fake = FakeWhoisResult(
        registrar="X",
        creation_date=[real_creation, real_creation + timedelta(days=10)],
        expiration_date=None,
        country="US",
    )
    _install_fake_whois(monkeypatch, lambda d: fake)
    result = _sync_whois("example.com")
    assert result is not None
    assert result["age_days"] == 50


def test_whois_missing_library_returns_none():
    """If the `whois` library isn't installed, the function should return None.

    We force ImportError by passing a name that cannot be imported.
    """
    # Temporarily hide `whois` from sys.modules and block the import.
    saved = sys.modules.pop("whois", None)
    saved_meta = sys.meta_path[:]

    class _BlockWhois:
        def find_spec(self, name, path=None, target=None):
            if name == "whois" or name.startswith("whois."):
                raise ImportError(f"blocked: {name}")
            return None

    blocker = _BlockWhois()
    sys.meta_path.insert(0, blocker)
    try:
        # Calling _sync_whois will trigger `import whois` inside the function,
        # which our meta-path blocker will reject -> caught by try/except -> None.
        assert _sync_whois("example.com") is None
    finally:
        sys.meta_path.remove(blocker)
        if saved is not None:
            sys.modules["whois"] = saved


def test_lookup_whois_async_timeout(monkeypatch):
    """If _sync_whois hangs longer than the 3s timeout, lookup_whois returns None."""
    def slow(domain):
        import time
        time.sleep(5)

    monkeypatch.setattr("app.services.phishshield.whois_lookup._sync_whois", slow)
    result = asyncio.run(lookup_whois("example.com"))
    assert result is None