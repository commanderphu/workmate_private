"""
Celery task: periodic Google Calendar sync for all users
"""

import asyncio
import logging

from ..celery import celery_app
from ..db.session import SessionLocal
from ..models.integration import Integration, IntegrationType
from ..models.user import User
from ..services.calendar_sync_service import CalendarSyncService

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.calendar_sync")
def calendar_sync():
    """
    Sync all active Google Calendar integrations.
    Runs every 15 minutes via celery beat.
    """
    db = SessionLocal()
    try:
        integrations = (
            db.query(Integration)
            .filter(
                Integration.integration_type == IntegrationType.GOOGLE_CALENDAR,
                Integration.is_active == True,
            )
            .all()
        )

        if not integrations:
            return {"synced": 0}

        sync_service = CalendarSyncService(db)
        synced = 0
        errors = 0

        for integration in integrations:
            user = db.query(User).filter(User.id == integration.user_id).first()
            if not user:
                continue
            try:
                result = asyncio.get_event_loop().run_until_complete(
                    sync_service.sync_integration(integration, user)
                )
                if result.errors == 0:
                    synced += 1
                else:
                    errors += 1
                    logger.warning(
                        f"Calendar sync user={user.id} errors: {result.error_messages}"
                    )
            except Exception as e:
                errors += 1
                logger.error(f"Calendar sync failed for integration {integration.id}: {e}")

        logger.info(f"Calendar sync done: {synced} ok, {errors} errors")
        return {"synced": synced, "errors": errors}

    finally:
        db.close()
