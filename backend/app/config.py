from typing import List

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


DEFAULT_DEV_DATABASE_URL = "sqlite+pysqlite:///./backend/data/sentinelx_dev.db"
TEST_DATABASE_URL = "sqlite+pysqlite:///:memory:"

_INVALID_DATABASE_URL_PLACEHOLDERS = {
    "",
    "your_database_url_here",
    "database_url_here",
    "<database_url>",
}
_PRODUCTION_ENVIRONMENTS = {"prod", "production"}


class Settings(BaseSettings):
    APP_NAME: str = "SentinelX"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    DATABASE_URL: str = DEFAULT_DEV_DATABASE_URL
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        database_url = value.strip()
        if database_url.lower() in _INVALID_DATABASE_URL_PLACEHOLDERS:
            raise ValueError("DATABASE_URL must be a valid SQLAlchemy URL, not a placeholder.")

        try:
            make_url(database_url)
        except ArgumentError as exc:
            raise ValueError("DATABASE_URL must be a valid SQLAlchemy URL.") from exc

        return database_url

    @model_validator(mode="after")
    def validate_production_database_url(self) -> "Settings":
        if (
            self.APP_ENV.strip().lower() in _PRODUCTION_ENVIRONMENTS
            and self.DATABASE_URL == DEFAULT_DEV_DATABASE_URL
        ):
            raise ValueError("APP_ENV=production requires an explicit production DATABASE_URL.")

        return self

    @property
    def origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]


settings = Settings()
