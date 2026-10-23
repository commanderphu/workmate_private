"""
Tests for ReminderService: priority/contract schedules, channels, due reminders
"""

from datetime import datetime, timedelta

import pytest

from app.models import Reminder, Task, User
from app.models.reminder import ReminderSeverity, ReminderStatus
from app.services.reminder_service import ReminderService

service = ReminderService()


@pytest.fixture()
def user(db):
    u = User(username="reminder", email="reminder@example.com", password_hash="x")
    db.add(u)
    db.commit()
    return u


@pytest.fixture()
def make_task(db, user):
    def _make(priority="medium", due_in_days=60):
        due = None if due_in_days is None else datetime.utcnow() + timedelta(days=due_in_days)
        task = Task(user_id=user.id, title="Testaufgabe", priority=priority, due_date=due)
        db.add(task)
        db.commit()
        return task

    return _make


def schedule_of(reminders, task):
    """(days_before, severity) pairs, sorted by days_before"""
    return sorted(
        (round((task.due_date - r.trigger_at) / timedelta(days=1)), r.severity) for r in reminders
    )


class TestPrioritySchedule:
    @pytest.mark.parametrize(
        "priority, expected",
        [
            ("critical", [(0, ReminderSeverity.CRITICAL), (1, ReminderSeverity.URGENT), (3, ReminderSeverity.WARNING)]),
            ("high", [(0, ReminderSeverity.URGENT), (2, ReminderSeverity.WARNING), (7, ReminderSeverity.INFO)]),
            ("medium", [(0, ReminderSeverity.WARNING), (3, ReminderSeverity.INFO)]),
            ("low", [(0, ReminderSeverity.INFO)]),
        ],
    )
    def test_schedule_per_priority(self, db, make_task, priority, expected):
        task = make_task(priority=priority)
        reminders = service.create_reminders_for_task(task, db)
        assert schedule_of(reminders, task) == expected
        assert all(r.status == ReminderStatus.PENDING for r in reminders)

    def test_unknown_priority_falls_back_to_medium(self, db, make_task):
        task = make_task(priority="irgendwas")
        reminders = service.create_reminders_for_task(task, db)
        assert schedule_of(reminders, task) == [(0, ReminderSeverity.WARNING), (3, ReminderSeverity.INFO)]

    def test_reminders_are_persisted(self, db, make_task):
        task = make_task(priority="critical")
        service.create_reminders_for_task(task, db)
        assert db.query(Reminder).filter(Reminder.task_id == task.id).count() == 3


class TestContractSchedule:
    def test_contract_schedule(self, db, make_task):
        task = make_task(due_in_days=90)
        reminders = service.create_reminders_for_task(task, db, schedule_type="contract")
        assert schedule_of(reminders, task) == [
            (1, ReminderSeverity.CRITICAL),
            (7, ReminderSeverity.URGENT),
            (14, ReminderSeverity.WARNING),
            (30, ReminderSeverity.INFO),
        ]

    def test_contract_close_to_deadline_skips_past_reminders(self, db, make_task):
        task = make_task(due_in_days=10)
        reminders = service.create_reminders_for_task(task, db, schedule_type="contract")
        assert schedule_of(reminders, task) == [(1, ReminderSeverity.CRITICAL), (7, ReminderSeverity.URGENT)]


class TestEdgeCases:
    def test_no_due_date_creates_nothing(self, db, make_task):
        task = make_task(due_in_days=None)
        assert service.create_reminders_for_task(task, db) == []

    def test_past_reminders_are_skipped(self, db, make_task):
        task = make_task(priority="critical", due_in_days=2)
        reminders = service.create_reminders_for_task(task, db)
        assert schedule_of(reminders, task) == [(0, ReminderSeverity.CRITICAL), (1, ReminderSeverity.URGENT)]

    def test_overdue_task_gets_immediate_reminder(self, db, make_task):
        task = make_task(priority="high", due_in_days=-1)
        before = datetime.utcnow()
        reminders = service.create_reminders_for_task(task, db)

        assert len(reminders) == 1
        assert reminders[0].severity == ReminderSeverity.URGENT
        assert before <= reminders[0].trigger_at <= datetime.utcnow()


class TestChannels:
    def test_default_channels_by_severity(self, db, make_task):
        task = make_task(priority="critical")
        by_severity = {r.severity: r.channels for r in service.create_reminders_for_task(task, db)}
        assert by_severity[ReminderSeverity.CRITICAL] == ["push", "email"]
        assert by_severity[ReminderSeverity.URGENT] == ["push", "email"]
        assert by_severity[ReminderSeverity.WARNING] == ["push"]

    def test_custom_channels_override_defaults(self, db, make_task):
        task = make_task(priority="critical")
        reminders = service.create_reminders_for_task(task, db, channels=["push"])
        assert all(r.channels == ["push"] for r in reminders)


class TestDueReminders:
    def _reminder(self, db, task, trigger_at, **fields):
        r = Reminder(task_id=task.id, trigger_at=trigger_at, severity=ReminderSeverity.INFO, **fields)
        db.add(r)
        db.commit()
        return r

    def test_only_pending_past_unsnoozed_reminders_are_due(self, db, make_task):
        task = make_task()
        now = datetime.utcnow()
        due = self._reminder(db, task, now - timedelta(minutes=5), status=ReminderStatus.PENDING)
        self._reminder(db, task, now + timedelta(hours=1), status=ReminderStatus.PENDING)
        self._reminder(db, task, now - timedelta(minutes=5), status=ReminderStatus.SENT)
        self._reminder(
            db, task, now - timedelta(minutes=5),
            status=ReminderStatus.PENDING, snoozed_until=now + timedelta(minutes=30),
        )

        assert [r.id for r in service.get_due_reminders(db)] == [due.id]

    def test_mark_sent_and_failed(self, db, make_task):
        task = make_task()
        sent = self._reminder(db, task, datetime.utcnow(), status=ReminderStatus.PENDING)
        failed = self._reminder(db, task, datetime.utcnow(), status=ReminderStatus.PENDING)

        service.mark_reminder_sent(sent, db)
        service.mark_reminder_sent(failed, db, error="FCM nicht erreichbar")

        assert sent.status == ReminderStatus.SENT and sent.sent_at is not None
        assert failed.status == ReminderStatus.FAILED and failed.error_message == "FCM nicht erreichbar"

    def test_cancel_removes_only_pending(self, db, make_task):
        task = make_task()
        self._reminder(db, task, datetime.utcnow(), status=ReminderStatus.PENDING)
        self._reminder(db, task, datetime.utcnow(), status=ReminderStatus.SENT)

        assert service.cancel_task_reminders(task.id, db) == 1
        assert [r.status for r in db.query(Reminder).all()] == [ReminderStatus.SENT]
