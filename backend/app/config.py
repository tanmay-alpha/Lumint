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
        "https://lumint-pi.vercel.app,"
        "https://*.vercel.app"
    )
    # Env-driven CORS allowlist. Read from the `CORS_ALLOW_ORIGINS` env var.
    # Accepts a JSON array (["https://a.com","https://b.com"]) OR a
    # comma-separated string ("https://a.com,https://b.com"). When the env
    # var is unset or empty, falls back to the localhost dev origins below.
    # In production, set this explicitly to the deployed frontend origin(s),
    # e.g. CORS_ALLOW_ORIGINS='["https://fraud-intelligence.vercel.app"]'
    #
    # IMPORTANT: default is `[]` (empty). The `origins_list` property below
    # must always read the env var at request time — a non-empty default
    # would shadow the env var and silently block production deploys
    # (this bug caused `lumint-pi.vercel.app` to be CORS-blocked).
    cors_allow_origins: list[str] = []

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
        """Build the CORS allowlist, reading from env vars at call time.

        Precedence (most specific first):
            1. `CORS_ALLOW_ORIGINS` env var — read raw via `os.getenv` so it
               picks up changes without a settings reload. Accepts a JSON
               array or a comma-separated string.
            2. The `cors_allow_origins` field (defaulted empty above).
            3. The legacy `ALLOWED_ORIGINS` field, which the project's
               `render.yaml` sets for free-tier deploys.
            4. Localhost dev defaults.

        We always re-read the env var because pydantic-settings caches
        `cors_allow_origins` at process start, and Render redeploys may
        rotate env vars between deploys.
        """
        import os  # local import to keep the module top-level importable

        raw = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
        if raw:
            parsed: list[str] = []
            # JSON-array form: ["https://a.com","https://b.com"]
            if raw.startswith("["):
                try:
                    import json
                    arr = json.loads(raw)
                    if isinstance(arr, list):
                        parsed = [str(x).strip() for x in arr if str(x).strip()]
                except Exception:
                    parsed = []
            if not parsed:
                # Comma-separated form: https://a.com,https://b.com
                parsed = [o.strip() for o in raw.split(",") if o.strip()]
            if parsed:
                return parsed

        if self.cors_allow_origins:
            return [o.strip() for o in self.cors_allow_origins if o.strip()]

        if self.ALLOWED_ORIGINS:
            return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

        return ["http://localhost:3000", "http://localhost:5173"]


settings = Settings()
