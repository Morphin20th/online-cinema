from pydantic_settings import SettingsConfigDict

from src.config.celery import CelerySettings
from src.config.database import DatabaseSettings
from src.config.email import EmailSettings
from src.config.payment import PaymentSettings
from src.config.security import SecuritySettings


class Settings(
    SecuritySettings, DatabaseSettings, CelerySettings, EmailSettings, PaymentSettings
):
    pass


class ProductionSettings(Settings):
    model_config = SettingsConfigDict(
        env_file=".env.prod",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class DevelopmentSettings(Settings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
