from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "Power Up API"
    DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key"

    # Database Settings
    DATABASE_URL: str = "postgresql+asyncpg://postgres:2025@localhost:5432/powerup_db"

    # OpenAI Settings
    OPENAI_API_KEY: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()



@lru_cache()
def get_settings():
    return settings