"""
Celery configuration for background tasks
"""

from celery import Celery
from .core.config import settings

celery_app = Celery(
    "workmate",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Use default queue (celery) for all tasks
# celery_app.conf.task_routes = {
#     "app.tasks.*": "main-queue",
# }

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Auto-discover tasks: imports app.tasks (__init__.py) which re-exports all task modules
celery_app.autodiscover_tasks(['app'])

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
}
