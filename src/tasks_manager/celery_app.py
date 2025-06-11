from celery import Celery
from celery.schedules import crontab

from src.config import get_settings

celery_app = Celery("cinema")
celery_app.conf.broker_url = get_settings().CELERY_URL
celery_app.conf.result_backend = get_settings().CELERY_URL
celery_app.conf.timezone = "UTC"

import src.tasks_manager.tasks.cleanup  # noqa

celery_app.conf.beat_schedule = {
    "delete-expired-tokens-every-minute": {
        "task": "src.tasks_manager.tasks.cleanup.delete_expired_tokens",
        "schedule": crontab(minute="*/1"),
    }
}
