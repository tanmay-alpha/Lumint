from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "SentinelX"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/sentinelx"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

    # Pydantic v2 style — removes deprecation warning
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]


settings = Settings()