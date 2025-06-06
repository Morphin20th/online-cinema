from fastapi import Depends

from security.token_manager import JWTManager
from .config import Settings, BaseAppSettings


def get_settings() -> Settings:
    return Settings()


def get_jwt_auth_manager(
    settings: BaseAppSettings = Depends(get_settings),
) -> JWTManager:
    return JWTManager(
        secret_key_access=settings.SECRET_KEY_ACCESS,
        secret_key_refresh=settings.SECRET_KEY_REFRESH,
        algorithm=settings.JWT_SIGNING_ALGORITHM,
    )
