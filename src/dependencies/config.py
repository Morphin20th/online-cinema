from fastapi import Depends
from redis import Redis

from src.services import EmailSender
from src.config.config import Settings, BaseAppSettings


def get_settings() -> Settings:
    return Settings()


def get_email_sender(settings: BaseAppSettings = Depends(get_settings)) -> EmailSender:
    return EmailSender(
        # email_host_password=settings.EMAIL_HOST_PASSWORD,
        email_host=settings.EMAIL_HOST,
        email_port=settings.EMAIL_PORT,
        email_host_user=settings.EMAIL_HOST_USER,
        from_email=settings.FROM_EMAIL,
        app_url=settings.APP_URL,
        project_root=settings.PROJECT_ROOT,
    )


def get_redis_client():
    return Redis(
        host=get_settings().REDIS_HOST,
        port=get_settings().REDIS_PORT,
        db=get_settings().REDIS_DB,
        decode_responses=True,
    )
