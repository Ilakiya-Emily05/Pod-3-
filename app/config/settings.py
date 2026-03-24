from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "powerup-api"
    debug: bool = True

    api_v1_prefix: str = "/api/v1"

    secret_key: str = "change-me-to-a-long-random-secret-key-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/powerup_db"

    cors_origins: str = "*"
    google_tokeninfo_url: str = "https://oauth2.googleapis.com/tokeninfo"
    google_token_url: str = "https://oauth2.googleapis.com/token"
    google_client_id: str | None = None
    google_client_secret: str | None = None
    admin_email: str | None = None
    admin_password: str | None = None

    @model_validator(mode="after")
    def validate_secret_key_for_production(self) -> "Settings":
        if (
            not self.debug
            and self.secret_key == "change-me-to-a-long-random-secret-key-in-production"
        ):
            msg = "SECRET_KEY must be overridden in non-debug environments"
            raise ValueError(msg)
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
