from pydantic_settings import BaseSettings
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    DATABASE_URL: str

    class Config:
        env_file = str(env_path)
        env_file_encoding = "utf-8"

settings = Settings()