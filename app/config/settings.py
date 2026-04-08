from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "powerup-api"
    app_env: str = "development"  # development | staging | production
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
    admin_password_hash: str | None = None

    # AI Settings
    openai_api_key: str | None = None
    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_api_version: str = "2024-02-01"

    # Pod-3 Compatibility
    @property
    def OPENAI_API_KEY(self) -> str | None:
        return self.openai_api_key

    @property
    def DEBUG(self) -> bool:
        return self.debug

    @property
    def PROJECT_NAME(self) -> str:
        return self.app_name

    @field_validator("debug", mode="before")
    @classmethod
    def coerce_debug(cls, value):  # noqa: ANN001
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "prod", "production"}:
                return False
            if normalized in {"dev", "development"}:
                return True
        return value

    @model_validator(mode="after")
    def validate_secret_key_for_production(self) -> "Settings":
        env = (self.app_env or "").strip().lower()
        is_development = env in {"development", "dev", "local"}
        if (
            not is_development
            and self.secret_key == "change-me-to-a-long-random-secret-key-in-production"
        ):
            msg = "SECRET_KEY must be overridden outside development"
            raise ValueError(msg)
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
