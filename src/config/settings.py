from src.config.celery import CelerySettings
from src.config.database import DatabaseSettings
from src.config.email import EmailSettings
from src.config.security import SecuritySettings


class Settings(SecuritySettings, DatabaseSettings, CelerySettings, EmailSettings):
    pass
