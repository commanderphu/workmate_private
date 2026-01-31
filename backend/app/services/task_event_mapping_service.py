"""
Task-Event Mapping Service
Automatically creates and syncs calendar events from tasks with deadlines
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import logging

from ..models import Task, CalendarEvent, Integration, User
from ..models.calendar_event import CalendarSyncStatus
from ..models.integration import SyncDirection

logger = logging.getLogger(__name__)


class TaskEventMappingService:
    """Service for mapping tasks to calendar events"""

    def __init__(self, db: Session):
        self.db = db

    def create_event_from_task(
        self,
        task: Task,
        integration_id: Optional[str] = None,
        auto_sync: bool = True
    ) -> Optional[CalendarEvent]:
        """
        Create a calendar event from a task

        Args:
            task: Task to create event from
            integration_id: Optional integration to sync to (if None, uses default or creates local-only event)
            auto_sync: Whether to automatically sync to external calendar

        Returns:
            Created CalendarEvent or None if task has no due_date
        """
        # Only create event if task has a due_date
        if not task.due_date:
            logger.debug(f"Task {task.id} has no due_date, skipping event creation")
            return None

        # Check if event already exists
        if task.calendar_event:
            logger.debug(f"Task {task.id} already has a calendar event")
            return task.calendar_event

        # Determine event duration
        if task.estimated_duration_minutes:
            duration = timedelta(minutes=task.estimated_duration_minutes)
        else:
            # Default to 1 hour
            duration = timedelta(hours=1)

        # Calculate start and end times
        # For tasks, we treat due_date as the deadline, so event ends at due_date
        end_time = task.due_date
        start_time = end_time - duration

        # Create title with task priority indicator
        priority_emoji = {
            "low": "🔵",
            "medium": "🟡",
            "high": "🟠",
            "critical": "🔴"
        }
        emoji = priority_emoji.get(task.priority, "📋")
        title = f"{emoji} {task.title}"

        # Create description with task details
        description_parts = []
        if task.description:
            description_parts.append(task.description)
        description_parts.append(f"\nStatus: {task.status}")
        description_parts.append(f"Priority: {task.priority}")
        if task.amount:
            description_parts.append(f"Amount: {task.amount} {task.currency}")
        description = "\n".join(description_parts)

        # Validate integration if provided
        if integration_id:
            integration = self.db.query(Integration).filter(
                Integration.id == integration_id,
                Integration.user_id == task.user_id
            ).first()
            if not integration:
                logger.warning(f"Integration {integration_id} not found, creating local-only event")
                integration_id = None

        # Create calendar event
        new_event = CalendarEvent(
            user_id=task.user_id,
            task_id=str(task.id),
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            all_day=False,
            external_calendar_id=integration_id,
            sync_status=CalendarSyncStatus.PENDING if (integration_id and auto_sync) else CalendarSyncStatus.SYNCED
        )

        self.db.add(new_event)
        self.db.commit()
        self.db.refresh(new_event)

        logger.info(f"Created calendar event for task {task.id}: {new_event.id}")
        return new_event

    def update_event_from_task(self, task: Task) -> Optional[CalendarEvent]:
        """
        Update existing calendar event when task changes

        Args:
            task: Updated task

        Returns:
            Updated CalendarEvent or None
        """
        event = task.calendar_event

        if not task.due_date:
            # Task no longer has due_date - delete event if exists
            if event:
                logger.info(f"Task {task.id} no longer has due_date, deleting event {event.id}")
                self.db.delete(event)
                self.db.commit()
            return None

        if not event:
            # No event exists but task now has due_date - create one
            logger.info(f"Task {task.id} now has due_date, creating event")
            return self.create_event_from_task(task)

        # Update existing event
        # Recalculate duration
        if task.estimated_duration_minutes:
            duration = timedelta(minutes=task.estimated_duration_minutes)
        else:
            duration = timedelta(hours=1)

        end_time = task.due_date
        start_time = end_time - duration

        # Update title with priority
        priority_emoji = {
            "low": "🔵",
            "medium": "🟡",
            "high": "🟠",
            "critical": "🔴"
        }
        emoji = priority_emoji.get(task.priority, "📋")
        title = f"{emoji} {task.title}"

        # Update description
        description_parts = []
        if task.description:
            description_parts.append(task.description)
        description_parts.append(f"\nStatus: {task.status}")
        description_parts.append(f"Priority: {task.priority}")
        if task.amount:
            description_parts.append(f"Amount: {task.amount} {task.currency}")
        description = "\n".join(description_parts)

        # Check if anything actually changed
        changed = (
            event.title != title or
            event.description != description or
            event.start_time != start_time or
            event.end_time != end_time
        )

        if changed:
            event.title = title
            event.description = description
            event.start_time = start_time
            event.end_time = end_time

            # Mark for re-sync if it was previously synced
            if event.sync_status == CalendarSyncStatus.SYNCED and event.external_calendar_id:
                event.sync_status = CalendarSyncStatus.PENDING

            self.db.commit()
            self.db.refresh(event)
            logger.info(f"Updated calendar event {event.id} for task {task.id}")
        else:
            logger.debug(f"No changes to event {event.id} for task {task.id}")

        return event

    def get_default_integration(self, user_id: str) -> Optional[Integration]:
        """
        Get default calendar integration for a user

        Returns first enabled integration with bidirectional or to_calendar sync
        """
        integration = self.db.query(Integration).filter(
            Integration.user_id == user_id,
            Integration.enabled == True,
            Integration.sync_direction.in_([
                SyncDirection.BIDIRECTIONAL,
                SyncDirection.TO_CALENDAR
            ])
        ).first()

        return integration

    def sync_task_to_calendar(self, task: Task, force: bool = False) -> bool:
        """
        Ensure task has a calendar event and sync it

        Args:
            task: Task to sync
            force: Force recreation of event even if one exists

        Returns:
            True if event was created/updated successfully
        """
        try:
            if force and task.calendar_event:
                # Delete existing event and recreate
                self.db.delete(task.calendar_event)
                self.db.commit()

            if task.calendar_event:
                # Update existing event
                self.update_event_from_task(task)
            else:
                # Create new event with default integration
                default_integration = self.get_default_integration(task.user_id)
                integration_id = str(default_integration.id) if default_integration else None
                self.create_event_from_task(task, integration_id=integration_id)

            return True

        except Exception as e:
            logger.error(f"Failed to sync task {task.id} to calendar: {e}")
            return False

    def bulk_sync_user_tasks(self, user: User, force: bool = False) -> dict:
        """
        Sync all tasks with due_dates for a user

        Args:
            user: User to sync tasks for
            force: Force recreation of all events

        Returns:
            Dictionary with sync statistics
        """
        stats = {
            "processed": 0,
            "created": 0,
            "updated": 0,
            "deleted": 0,
            "errors": 0
        }

        try:
            # Get all tasks with due_dates
            tasks = self.db.query(Task).filter(
                Task.user_id == user.id,
                Task.due_date.isnot(None)
            ).all()

            for task in tasks:
                try:
                    stats["processed"] += 1

                    if force and task.calendar_event:
                        self.db.delete(task.calendar_event)
                        self.db.commit()
                        stats["deleted"] += 1

                    if task.calendar_event:
                        self.update_event_from_task(task)
                        stats["updated"] += 1
                    else:
                        default_integration = self.get_default_integration(user.id)
                        integration_id = str(default_integration.id) if default_integration else None
                        self.create_event_from_task(task, integration_id=integration_id)
                        stats["created"] += 1

                except Exception as e:
                    logger.error(f"Error syncing task {task.id}: {e}")
                    stats["errors"] += 1

            # Also clean up events for tasks without due_dates
            orphaned_events = self.db.query(CalendarEvent).join(Task).filter(
                CalendarEvent.user_id == user.id,
                CalendarEvent.task_id.isnot(None),
                Task.due_date.is_(None)
            ).all()

            for event in orphaned_events:
                self.db.delete(event)
                stats["deleted"] += 1

            self.db.commit()
            logger.info(f"Bulk sync completed for user {user.id}: {stats}")

        except Exception as e:
            logger.error(f"Bulk sync failed for user {user.id}: {e}")
            stats["errors"] += 1
            self.db.rollback()

        return stats

    def remove_completed_task_events(self, user: User, older_than_days: int = 7) -> int:
        """
        Remove calendar events for completed tasks older than X days

        Args:
            user: User to clean up events for
            older_than_days: Remove events for tasks completed more than X days ago

        Returns:
            Number of events deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)

            events = self.db.query(CalendarEvent).join(Task).filter(
                CalendarEvent.user_id == user.id,
                CalendarEvent.task_id.isnot(None),
                Task.status.in_(["done", "cancelled"]),
                Task.completed_at < cutoff_date
            ).all()

            count = len(events)
            for event in events:
                self.db.delete(event)

            self.db.commit()
            logger.info(f"Removed {count} completed task events for user {user.id}")
            return count

        except Exception as e:
            logger.error(f"Failed to remove completed task events: {e}")
            self.db.rollback()
            return 0
