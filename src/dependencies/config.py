from fastapi import Depends
from redis import Redis

from src.config import Settings, get_settings
from src.services import EmailSenderInterface, StripeServiceInterface
from src.services.email_service import EmailSender
from src.services.stripe import StripeService


def get_email_sender(
    settings: Settings = Depends(get_settings),
) -> EmailSenderInterface:
    """
    Dependency that provides an instance of the email sending service.

    Args:
        settings (Settings): Application settings injected via Depends.

    Returns:
        EmailSenderInterface: An instance of EmailSender for sending emails.
    """
    return EmailSender(
        email_host=settings.EMAIL_HOST,
        email_port=settings.EMAIL_PORT,
        email_host_user=settings.EMAIL_HOST_USER,
        from_email=settings.FROM_EMAIL,
        app_url=settings.APP_URL,
        project_root=settings.PROJECT_ROOT,
    )


def get_redis_client(settings: Settings = Depends(get_settings)) -> Redis:
    """
    Dependency that provides a configured Redis client.

    Args:
        settings (Settings): Application settings injected via Depends.

    Returns:
        Redis: Redis client instance connected to configured host and port.
    """
    return Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        decode_responses=True,
    )


def get_stripe_service(
    settings: Settings = Depends(get_settings),
) -> StripeServiceInterface:
    """
    Dependency that provides a configured Stripe service for handling payments.

    Args:
        settings (Settings): Application settings injected via Depends.

    Returns:
        StripeServiceInterface: An instance of StripeService to manage Stripe API.
    """
    return StripeService(
        api_key=settings.STRIPE_SECRET_KEY,
        webhook_key=settings.STRIPE_WEBHOOK_SECRET,
        app_url=settings.APP_URL,
    )
