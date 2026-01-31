"""
Calendar Sync Service
Handles bidirectional synchronization between local calendar events and external calendars
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import logging

from ..models import CalendarEvent, Integration, User
from ..models.calendar_event import CalendarSyncStatus
from ..models.integration import IntegrationType, SyncDirection
from .caldav_service import CalDAVService

logger = logging.getLogger(__name__)


class SyncResult:
    """Result of a sync operation"""
    def __init__(self):
        self.events_pushed = 0  # Local → External
        self.events_pulled = 0  # External → Local
        self.events_updated = 0  # Updated on either side
        self.conflicts = 0
        self.errors = 0
        self.error_messages: List[str] = []

    def to_dict(self) -> Dict:
        return {
            "events_pushed": self.events_pushed,
            "events_pulled": self.events_pulled,
            "events_updated": self.events_updated,
            "conflicts": self.conflicts,
            "errors": self.errors,
            "error_messages": self.error_messages,
            "total_synced": self.events_pushed + self.events_pulled + self.events_updated
        }


class CalendarSyncService:
    """Service for synchronizing calendar events with external calendars"""

    def __init__(self, db: Session):
        self.db = db

    async def sync_integration(self, integration: Integration, user: User) -> SyncResult:
        """
        Sync an integration based on its sync_direction

        Args:
            integration: Integration to sync
            user: User who owns the integration

        Returns:
            SyncResult with statistics
        """
        result = SyncResult()

        try:
            if integration.integration_type == IntegrationType.CALDAV:
                result = await self._sync_caldav(integration, user)
            elif integration.integration_type == IntegrationType.GOOGLE_CALENDAR:
                # TODO: Implement Google Calendar sync
                logger.warning("Google Calendar sync not yet implemented")
                result.errors += 1
                result.error_messages.append("Google Calendar sync not yet implemented")
            elif integration.integration_type == IntegrationType.OUTLOOK_CALENDAR:
                # TODO: Implement Outlook Calendar sync
                logger.warning("Outlook Calendar sync not yet implemented")
                result.errors += 1
                result.error_messages.append("Outlook Calendar sync not yet implemented")

            # Update integration sync status
            integration.last_sync_at = datetime.utcnow()
            if result.errors == 0:
                integration.sync_status = "success"
                integration.error_log = None
            else:
                integration.sync_status = "error"
                integration.error_log = "; ".join(result.error_messages)

            self.db.commit()

        except Exception as e:
            logger.error(f"Failed to sync integration {integration.id}: {e}")
            integration.sync_status = "error"
            integration.error_log = str(e)
            self.db.commit()
            result.errors += 1
            result.error_messages.append(str(e))

        return result

    async def _sync_caldav(self, integration: Integration, user: User) -> SyncResult:
        """
        Sync CalDAV integration

        Args:
            integration: CalDAV integration
            user: User who owns the integration

        Returns:
            SyncResult with statistics
        """
        result = SyncResult()

        try:
            # Initialize CalDAV service
            caldav_service = CalDAVService(
                url=integration.config.get('url'),
                username=integration.credentials.get('username'),
                password=integration.credentials.get('password')
            )

            calendar_name = integration.config.get('calendar_name')

            # Sync based on direction
            if integration.sync_direction == SyncDirection.FROM_CALENDAR:
                # Only pull from external calendar
                await self._pull_from_caldav(caldav_service, calendar_name, integration, user, result)

            elif integration.sync_direction == SyncDirection.TO_CALENDAR:
                # Only push to external calendar
                await self._push_to_caldav(caldav_service, calendar_name, integration, user, result)

            elif integration.sync_direction == SyncDirection.BIDIRECTIONAL:
                # Both directions - pull first, then push
                await self._pull_from_caldav(caldav_service, calendar_name, integration, user, result)
                await self._push_to_caldav(caldav_service, calendar_name, integration, user, result)

        except Exception as e:
            logger.error(f"CalDAV sync error: {e}")
            result.errors += 1
            result.error_messages.append(f"CalDAV error: {str(e)}")

        return result

    async def _pull_from_caldav(
        self,
        caldav_service: CalDAVService,
        calendar_name: str,
        integration: Integration,
        user: User,
        result: SyncResult
    ):
        """
        Pull events from external CalDAV calendar to local database

        Creates new events or updates existing ones
        """
        try:
            # Fetch events from last 30 days to next 365 days
            start_date = datetime.now() - timedelta(days=30)
            end_date = datetime.now() + timedelta(days=365)

            external_events = await caldav_service.fetch_events(
                calendar_name=calendar_name,
                start_date=start_date,
                end_date=end_date
            )

            for ext_event in external_events:
                try:
                    # Check if event already exists locally
                    local_event = self.db.query(CalendarEvent).filter(
                        CalendarEvent.external_event_id == ext_event['external_id'],
                        CalendarEvent.user_id == user.id
                    ).first()

                    if local_event:
                        # Event exists - check for conflicts
                        conflict = self._detect_conflict(local_event, ext_event)

                        if conflict:
                            # Store conflict data and mark as conflict
                            local_event.sync_status = CalendarSyncStatus.CONFLICT
                            local_event.conflict_data = {
                                "local": {
                                    "title": local_event.title,
                                    "start_time": local_event.start_time.isoformat(),
                                    "end_time": local_event.end_time.isoformat(),
                                    "description": local_event.description,
                                    "location": local_event.location,
                                },
                                "remote": {
                                    "title": ext_event['title'],
                                    "start_time": ext_event['start'].isoformat(),
                                    "end_time": ext_event['end'].isoformat(),
                                    "description": ext_event['description'],
                                    "location": ext_event['location'],
                                },
                                "detected_at": datetime.utcnow().isoformat()
                            }
                            result.conflicts += 1
                            logger.warning(f"Conflict detected for event {local_event.id}")

                        elif local_event.last_synced_at and ext_event.get('last_modified'):
                            # Remote is newer - update local
                            if ext_event['last_modified'] > local_event.last_synced_at:
                                self._update_local_event(local_event, ext_event)
                                result.events_updated += 1
                                logger.info(f"Updated local event {local_event.id} from remote")
                    else:
                        # New event from external calendar - create locally
                        new_event = CalendarEvent(
                            user_id=user.id,
                            title=ext_event['title'],
                            description=ext_event.get('description', ''),
                            start_time=ext_event['start'],
                            end_time=ext_event['end'],
                            location=ext_event.get('location', ''),
                            external_event_id=ext_event['external_id'],
                            external_calendar_id=integration.id,
                            sync_status=CalendarSyncStatus.SYNCED,
                            last_synced_at=datetime.utcnow()
                        )
                        self.db.add(new_event)
                        result.events_pulled += 1
                        logger.info(f"Created new local event from external: {ext_event['title']}")

                except Exception as e:
                    logger.error(f"Error processing event {ext_event.get('title', 'unknown')}: {e}")
                    result.errors += 1
                    result.error_messages.append(f"Event pull error: {str(e)}")

            self.db.commit()

        except Exception as e:
            logger.error(f"Failed to pull from CalDAV: {e}")
            result.errors += 1
            result.error_messages.append(f"Pull error: {str(e)}")

    async def _push_to_caldav(
        self,
        caldav_service: CalDAVService,
        calendar_name: str,
        integration: Integration,
        user: User,
        result: SyncResult
    ):
        """
        Push local events to external CalDAV calendar

        Only pushes events that are pending sync or haven't been synced yet
        """
        try:
            # Get local events that need syncing
            pending_events = self.db.query(CalendarEvent).filter(
                CalendarEvent.user_id == user.id,
                CalendarEvent.external_calendar_id == integration.id,
                CalendarEvent.sync_status.in_([CalendarSyncStatus.PENDING, CalendarSyncStatus.FAILED])
            ).all()

            for local_event in pending_events:
                try:
                    if local_event.external_event_id:
                        # Update existing event
                        await caldav_service.update_event(
                            event_id=local_event.external_event_id,
                            title=local_event.title,
                            start=local_event.start_time,
                            end=local_event.end_time,
                            description=local_event.description,
                            location=local_event.location
                        )
                        result.events_updated += 1
                        logger.info(f"Updated remote event {local_event.external_event_id}")
                    else:
                        # Create new event
                        external_id = await caldav_service.create_event(
                            calendar_name=calendar_name,
                            title=local_event.title,
                            start=local_event.start_time,
                            end=local_event.end_time,
                            description=local_event.description,
                            location=local_event.location
                        )
                        local_event.external_event_id = external_id
                        result.events_pushed += 1
                        logger.info(f"Created new remote event: {local_event.title}")

                    # Mark as synced
                    local_event.sync_status = CalendarSyncStatus.SYNCED
                    local_event.last_synced_at = datetime.utcnow()

                except Exception as e:
                    logger.error(f"Error pushing event {local_event.id}: {e}")
                    local_event.sync_status = CalendarSyncStatus.FAILED
                    result.errors += 1
                    result.error_messages.append(f"Event push error: {str(e)}")

            self.db.commit()

        except Exception as e:
            logger.error(f"Failed to push to CalDAV: {e}")
            result.errors += 1
            result.error_messages.append(f"Push error: {str(e)}")

    def _detect_conflict(self, local_event: CalendarEvent, external_event: Dict) -> bool:
        """
        Detect if there's a conflict between local and external event

        A conflict occurs when both local and external events have been modified
        since the last sync
        """
        if not local_event.last_synced_at:
            return False

        # Check if local event was modified after last sync
        local_modified = local_event.updated_at > local_event.last_synced_at

        # Check if external event was modified after last sync
        external_modified = False
        if external_event.get('last_modified'):
            external_modified = external_event['last_modified'] > local_event.last_synced_at

        # Conflict if both were modified
        return local_modified and external_modified

    def _update_local_event(self, local_event: CalendarEvent, external_event: Dict):
        """
        Update local event with data from external event
        """
        local_event.title = external_event['title']
        local_event.description = external_event.get('description', '')
        local_event.start_time = external_event['start']
        local_event.end_time = external_event['end']
        local_event.location = external_event.get('location', '')
        local_event.sync_status = CalendarSyncStatus.SYNCED
        local_event.last_synced_at = datetime.utcnow()
        local_event.conflict_data = None  # Clear any previous conflict data

    async def resolve_conflict(
        self,
        event_id: str,
        resolution: str,  # 'keep_local' or 'keep_remote'
        user: User
    ) -> bool:
        """
        Resolve a conflict for a calendar event

        Args:
            event_id: ID of the conflicted event
            resolution: 'keep_local' to keep local changes, 'keep_remote' to accept remote changes
            user: User who owns the event

        Returns:
            True if resolved successfully
        """
        event = self.db.query(CalendarEvent).filter(
            CalendarEvent.id == event_id,
            CalendarEvent.user_id == user.id,
            CalendarEvent.sync_status == CalendarSyncStatus.CONFLICT
        ).first()

        if not event or not event.conflict_data:
            return False

        try:
            if resolution == 'keep_remote' and event.conflict_data.get('remote'):
                # Update local event with remote data
                remote_data = event.conflict_data['remote']
                event.title = remote_data['title']
                event.start_time = datetime.fromisoformat(remote_data['start_time'])
                event.end_time = datetime.fromisoformat(remote_data['end_time'])
                event.description = remote_data.get('description', '')
                event.location = remote_data.get('location', '')

            # For 'keep_local', we don't need to change local data,
            # just mark it for push in next sync

            # Clear conflict and mark as pending sync
            event.sync_status = CalendarSyncStatus.PENDING
            event.conflict_data = None
            event.last_synced_at = None  # Force re-sync

            self.db.commit()
            logger.info(f"Resolved conflict for event {event_id} with resolution: {resolution}")
            return True

        except Exception as e:
            logger.error(f"Failed to resolve conflict: {e}")
            self.db.rollback()
            return False
