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
