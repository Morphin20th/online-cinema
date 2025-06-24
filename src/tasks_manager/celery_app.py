from celery import Celery
from celery.schedules import crontab

from src.dependencies import get_settings


settings = get_settings()

celery_url = str(settings.CELERY_BROKER_URL)

celery_app = Celery("cinema")
celery_app.conf.broker_url = celery_url
celery_app.conf.result_backend = celery_url
celery_app.conf.timezone = "UTC"

import src.tasks_manager.tasks.cleanup  # noqa

celery_app.conf.beat_schedule = {
    "delete-expired-tokens-every-minute": {
        "task": "src.tasks_manager.tasks.cleanup.delete_expired_tokens",
        "schedule": crontab(minute="*/1"),
    }
}
