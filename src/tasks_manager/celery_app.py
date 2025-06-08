import os

from celery import Celery
from celery.schedules import crontab

celery_app = Celery("cinema")
celery_app.conf.broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
celery_app.conf.result_backend = os.getenv(
    "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
)
celery_app.conf.timezone = "UTC"

import src.tasks_manager.tasks.cleanup

celery_app.conf.beat_schedule = {
    "delete-expired-tokens-every-minute": {
        "task": "src.tasks_manager.tasks.cleanup.delete_expired_tokens",
        "schedule": crontab(minute="*/1"),
    }
}
