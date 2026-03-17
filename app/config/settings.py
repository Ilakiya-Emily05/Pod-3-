from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    app_name: str = "powerup-api"
    debug: bool = True

    api_v1_prefix: str = "/api/v1"

    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/powerup_db"

    cors_origins: str = "*"
    google_tokeninfo_url: str = "https://oauth2.googleapis.com/tokeninfo"
    google_token_url: str = "https://oauth2.googleapis.com/token"  # noqa: S105
    google_client_id: str | None = None
    google_client_secret: str | None = None

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
