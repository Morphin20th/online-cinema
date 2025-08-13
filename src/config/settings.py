from pydantic_settings import SettingsConfigDict

from src.config.api import APISettings
from src.config.celery import CelerySettings
from src.config.database import PostgreSQLSettings
from src.config.email import EmailSettings
from src.config.payment import PaymentSettings
from src.config.security import SecuritySettings


class Settings(
    SecuritySettings,
    PostgreSQLSettings,
    CelerySettings,
    EmailSettings,
    PaymentSettings,
    APISettings,
):
    pass


class ProductionSettings(Settings):
    model_config = SettingsConfigDict(
        env_file=".env.prod",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DEBUG: bool = False


class DevelopmentSettings(Settings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class TestingSettings(Settings):
    model_config = SettingsConfigDict(
        env_file=".env.test",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DEBUG: bool = False
    DB_NAME: str = "test_db"
    DB_HOST: str = "db"
