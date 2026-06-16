import pytest
from pydantic import ValidationError

from app.config import DEFAULT_DEV_DATABASE_URL, Settings, TEST_DATABASE_URL


def test_settings_accepts_test_database_url():
    test_settings = Settings(APP_ENV="test", DATABASE_URL=TEST_DATABASE_URL)

    assert test_settings.DATABASE_URL == TEST_DATABASE_URL


def test_settings_rejects_placeholder_database_url():
    with pytest.raises(ValidationError, match="DATABASE_URL"):
        Settings(DATABASE_URL="your_database_url_here")


def test_settings_rejects_default_database_url_in_production():
    with pytest.raises(ValidationError, match="production"):
        Settings(APP_ENV="production", DATABASE_URL=DEFAULT_DEV_DATABASE_URL)


def test_origins_list_defaults_to_localhost_only_when_cors_env_absent(monkeypatch):
    monkeypatch.delenv("CORS_ALLOW_ORIGINS", raising=False)
    test_settings = Settings(
        APP_ENV="test",
        DATABASE_URL=TEST_DATABASE_URL,
        ALLOWED_ORIGINS="",
        cors_allow_origins=[],
    )

    assert test_settings.origins_list == ["http://localhost:3000", "http://localhost:5173"]


def test_empty_json_cors_env_falls_back_to_localhost_defaults(monkeypatch):
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "[]")
    test_settings = Settings(
        APP_ENV="test",
        DATABASE_URL=TEST_DATABASE_URL,
        ALLOWED_ORIGINS="",
        cors_allow_origins=[],
    )

    assert test_settings.origins_list == ["http://localhost:3000", "http://localhost:5173"]


def test_default_origins_list_does_not_trust_wildcard_vercel(monkeypatch):
    monkeypatch.delenv("CORS_ALLOW_ORIGINS", raising=False)
    test_settings = Settings(APP_ENV="test", DATABASE_URL=TEST_DATABASE_URL)

    assert "https://*.vercel.app" not in test_settings.origins_list
