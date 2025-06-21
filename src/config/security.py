import secrets

from pydantic import SecretStr

from src.config.config import BaseAppSettings


class SecuritySettings(BaseAppSettings):
    # JWT Tokens
    SECRET_KEY_ACCESS: SecretStr = secrets.token_urlsafe(32)
    SECRET_KEY_REFRESH: SecretStr = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"

    # Token Lifetimes (in days)
    LOGIN_DAYS: int = 7
    ACTIVATION_TOKEN_LIFE: int = 1
