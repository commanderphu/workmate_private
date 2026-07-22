"""
Reminder Service for creating and managing reminders
"""

from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session

from ..models.reminder import Reminder, ReminderSeverity, ReminderStatus
from ..models.task import Task


class ReminderService:
    """Service for creating and managing task reminders"""

    # Reminder scheduling rules based on task priority
    REMINDER_SCHEDULE = {
        "critical": [
            {"days_before": 0, "severity": ReminderSeverity.CRITICAL},  # On due date
            {"days_before": 1, "severity": ReminderSeverity.URGENT},    # 1 day before
            {"days_before": 3, "severity": ReminderSeverity.WARNING},   # 3 days before
        ],
        "high": [
            {"days_before": 0, "severity": ReminderSeverity.URGENT},
            {"days_before": 2, "severity": ReminderSeverity.WARNING},
            {"days_before": 7, "severity": ReminderSeverity.INFO},
        ],
        "medium": [
            {"days_before": 0, "severity": ReminderSeverity.WARNING},
            {"days_before": 3, "severity": ReminderSeverity.INFO},
        ],
        "low": [
            {"days_before": 0, "severity": ReminderSeverity.INFO},
        ],
    }

    # Contract-specific schedule — much longer lead times for Kündigungsfristen
    CONTRACT_REMINDER_SCHEDULE = [
        {"days_before": 30, "severity": ReminderSeverity.INFO},
        {"days_before": 14, "severity": ReminderSeverity.WARNING},
        {"days_before": 7,  "severity": ReminderSeverity.URGENT},
        {"days_before": 1,  "severity": ReminderSeverity.CRITICAL},
    ]

    # Default notification channels based on severity
    DEFAULT_CHANNELS = {
        ReminderSeverity.CRITICAL: ["push", "email"],
        ReminderSeverity.URGENT: ["push", "email"],
        ReminderSeverity.WARNING: ["push"],
        ReminderSeverity.INFO: ["push"],
    }

    def create_reminders_for_task(
        self,
        task: Task,
        db: Session,
        channels: Optional[List[str]] = None,
        schedule_type: str = "priority"
    ) -> List[Reminder]:
        """
        Create reminders for a task based on its priority and due date

        Args:
            task: Task to create reminders for
            db: Database session
            channels: Custom notification channels (overrides defaults)
            schedule_type: "priority" (default) or "contract"

        Returns:
            List of created Reminder objects
        """
        if not task.due_date:
            return []

        if schedule_type == "contract":
            schedule = self.CONTRACT_REMINDER_SCHEDULE
        else:
            schedule = self.REMINDER_SCHEDULE.get(task.priority, self.REMINDER_SCHEDULE["medium"])

        created_reminders = []

        for reminder_config in schedule:
            days_before = reminder_config["days_before"]
            severity = reminder_config["severity"]

            # Calculate trigger time
            trigger_at = task.due_date - timedelta(days=days_before)

            # Don't create reminders in the past
            if trigger_at < datetime.utcnow():
                # For overdue tasks, create immediate reminder
                if days_before == 0:
                    trigger_at = datetime.utcnow()
                else:
                    continue

            # Determine notification channels
            if channels:
                reminder_channels = channels
            else:
                reminder_channels = self.DEFAULT_CHANNELS.get(severity, ["push"])

            # Create reminder
            reminder = Reminder(
                task_id=task.id,
                trigger_at=trigger_at,
                severity=severity,
                channels=reminder_channels,
                status=ReminderStatus.PENDING,
            )

            db.add(reminder)
            created_reminders.append(reminder)

        db.commit()

        return created_reminders

    def get_due_reminders(self, db: Session) -> List[Reminder]:
        """
        Get all pending reminders that are due to be sent

        Args:
            db: Database session

        Returns:
            List of due reminders
        """
        now = datetime.utcnow()

        reminders = (
            db.query(Reminder)
            .filter(
                Reminder.status == ReminderStatus.PENDING,
                Reminder.trigger_at <= now,
                Reminder.snoozed_until == None  # Not snoozed
            )
            .all()
        )

        return reminders

    def mark_reminder_sent(
        self,
        reminder: Reminder,
        db: Session,
        error: Optional[str] = None
    ) -> None:
        """
        Mark a reminder as sent or failed

        Args:
            reminder: Reminder to update
            db: Database session
            error: Error message if sending failed
        """
        if error:
            reminder.status = ReminderStatus.FAILED
            reminder.error_message = error
        else:
            reminder.status = ReminderStatus.SENT
            reminder.sent_at = datetime.utcnow()

        db.commit()

    def snooze_reminder(
        self,
        reminder: Reminder,
        db: Session,
        snooze_minutes: int = 60
    ) -> None:
        """
        Snooze a reminder for a specified duration

        Args:
            reminder: Reminder to snooze
            db: Database session
            snooze_minutes: How long to snooze (default: 60 minutes)
        """
        reminder.snoozed_until = datetime.utcnow() + timedelta(minutes=snooze_minutes)
        db.commit()

    def acknowledge_reminder(
        self,
        reminder: Reminder,
        db: Session
    ) -> None:
        """
        Mark a reminder as acknowledged by the user

        Args:
            reminder: Reminder to acknowledge
            db: Database session
        """
        reminder.acknowledged_at = datetime.utcnow()
        db.commit()

    def cancel_task_reminders(
        self,
        task_id: str,
        db: Session
    ) -> int:
        """
        Cancel all pending reminders for a task (e.g., when task is completed)

        Args:
            task_id: UUID of the task
            db: Database session

        Returns:
            Number of reminders cancelled
        """
        count = (
            db.query(Reminder)
            .filter(
                Reminder.task_id == task_id,
                Reminder.status == ReminderStatus.PENDING
            )
            .delete()
        )

        db.commit()

        return count
