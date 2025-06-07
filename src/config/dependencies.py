from fastapi import Depends

from security.token_manager import JWTManager
from services import EmailSender
from .config import Settings, BaseAppSettings


def get_settings() -> Settings:
    return Settings()


def get_jwt_auth_manager(
    settings: BaseAppSettings = Depends(get_settings),
) -> JWTManager:
    return JWTManager(
        secret_key_access=settings.SECRET_KEY_ACCESS,
        secret_key_refresh=settings.SECRET_KEY_REFRESH,
        algorithm=settings.ALGORITHM,
    )


def get_email_sender(settings: BaseAppSettings = Depends(get_settings)) -> EmailSender:
    return EmailSender(
        # email_host_password=settings.EMAIL_HOST_PASSWORD,
        email_host=settings.EMAIL_HOST,
        email_port=settings.EMAIL_PORT,
        email_host_user=settings.EMAIL_HOST_USER,
        from_email=settings.FROM_EMAIL,
    )
