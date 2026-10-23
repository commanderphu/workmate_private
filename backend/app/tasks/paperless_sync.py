"""
Celery task: periodic Paperless-ngx sync
"""

import logging
from datetime import datetime, timedelta

from ..celery import celery_app
from ..core.config import settings
from ..db.session import SessionLocal
from ..models.user import User
from ..services.paperless_service import PaperlessSyncService, get_paperless_client

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.paperless_sync")
def paperless_sync():
    """
    Pull new documents from Paperless for all users.
    Runs every 30 minutes via celery beat.
    Skips gracefully if Paperless is not configured.
    """
    if not settings.PAPERLESS_SYNC_ENABLED:
        logger.info("PAPERLESS_SYNC_ENABLED=false, skipping sync")
        return

    client = get_paperless_client()
    if not client:
        logger.debug("Paperless not configured, skipping sync")
        return

    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()
        since = datetime.utcnow() - timedelta(hours=48)

        for user in users:
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                svc = PaperlessSyncService(db=db, user_id=user.id)

                result = loop.run_until_complete(svc.import_new_documents(since=since))
                if result["imported"] > 0:
                    logger.info(
                        f"Paperless sync user={user.id}: "
                        f"{result['imported']} imported, {result['skipped']} skipped"
                    )

                wb = loop.run_until_complete(svc.push_workmate_changes())
                if wb["synced"] > 0:
                    logger.info(f"Paperless write-back user={user.id}: {wb['synced']} docs synced")

            except Exception as e:
                logger.error(f"Paperless sync failed for user {user.id}: {e}")
    finally:
        db.close()
