from src.config.config import BaseAppSettings


class EmailSettings(BaseAppSettings):
    EMAIL_HOST: str = "localhost"
    EMAIL_PORT: int = 1111
    EMAIL_HOST_USER: str = ""
    EMAIL_HOST_PASSWORD: str = ""
    FROM_EMAIL: str = "no-reply@example.com"
    EMAIL_USE_TLS: bool = False
