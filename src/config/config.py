import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class BaseAppSettings(BaseSettings):
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent.resolve()
    APP_URL: str = os.getenv("APP_URL", "http://127.0.0.1:8001")

    SECRET_KEY_ACCESS: str = os.getenv("SECRET_KEY_ACCESS", secrets.token_urlsafe(32))
    SECRET_KEY_REFRESH: str = os.getenv("SECRET_KEY_REFRESH", secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"

    LOGIN_DAYS: int = 1

    EMAIL_HOST: str = os.getenv("EMAIL_HOST", "localhost")
    EMAIL_PORT: int = os.getenv("EMAIL_PORT", 1111)
    EMAIL_HOST_USER: str = os.getenv("EMAIL_HOST_USER", "test_user")
    EMAIL_HOST_PASSWORD: str = os.getenv("EMAIL_HOST_PASSWORD", "test_password")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "no-reply@cinema.com")


class Settings(BaseAppSettings):
    DB_USER: str = os.getenv("DB_USER", "test_user")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = os.getenv("DB_PORT", 5432)
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "test_password")
    DB_NAME: str = os.getenv("DB_NAME", "test_name")

    @property
    def DATABASE_URL(self):
        return f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
