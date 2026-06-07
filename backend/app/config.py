from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

DEFAULT_DEV_DATABASE_URL = "sqlite+pysqlite:///./backend/data/lumint_dev.db"
TEST_DATABASE_URL = "sqlite+pysqlite:///:memory:"

_INVALID_PLACEHOLDERS = {"", "your_database_url_here", "database_url_here", "<database_url>"}
_PRODUCTION_ENVS = {"prod", "production"}


import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve absolute path to the backend/.env file and load it explicitly
backend_dir = Path(__file__).resolve().parents[1]
env_path = backend_dir / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    APP_NAME: str = "Lumint"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = False
    DATABASE_URL: str = DEFAULT_DEV_DATABASE_URL
    GROQ_API_KEY: str = ""
    # Comma-separated origins — set ALLOWED_ORIGINS in Vercel env vars
    ALLOWED_ORIGINS: str = (
        "http://localhost:3000,"
        "http://localhost:3001,"
        "https://lumint.vercel.app,"
        "https://*.vercel.app"
    )

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        v = v.strip()
        if v.lower() in _INVALID_PLACEHOLDERS:
            raise ValueError("DATABASE_URL must be a valid SQLAlchemy URL.")
        
        # If it points to ./backend/data/ but we are in the backend dir, adapt to ./data/
        import os
        if "sqlite" in v and "./backend/data/" in v:
            if not os.path.exists("./backend") and os.path.exists("./data"):
                v = v.replace("./backend/data/", "./data/")
                
        try:
            make_url(v)
        except ArgumentError as exc:
            raise ValueError("DATABASE_URL must be a valid SQLAlchemy URL.") from exc
        return v

    @model_validator(mode="after")
    def validate_production_db(self) -> "Settings":
        if self.APP_ENV.strip().lower() in _PRODUCTION_ENVS and (self.DATABASE_URL == DEFAULT_DEV_DATABASE_URL or "lumint_dev.db" in self.DATABASE_URL):
            raise ValueError("APP_ENV=production requires an explicit production DATABASE_URL.")
        return self

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


settings = Settings()
