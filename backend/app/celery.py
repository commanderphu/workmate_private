"""
Celery configuration for background tasks
"""

from celery import Celery
from .core.config import settings

celery_app = Celery(
    "workmate",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.document_processing",
        "app.tasks.reminder_dispatch",
        "app.tasks.paperless_sync",
        "app.tasks.paperless_analyze",
        "app.tasks.calendar_sync",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Beat schedule
celery_app.conf.beat_schedule = {
    "dispatch-reminders": {
        "task": "app.tasks.dispatch_reminders",
        "schedule": 60.0,  # every 60 seconds
    },
    "paperless-sync": {
        "task": "app.tasks.paperless_sync",
        "schedule": 1800.0,  # every 30 minutes
    },
    "calendar-sync": {
        "task": "app.tasks.calendar_sync",
        "schedule": 900.0,  # every 15 minutes
    },
}
