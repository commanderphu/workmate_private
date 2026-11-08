"""
Tests for the Paperless import -> AI analysis pipeline and the periodic calendar sync
"""

from datetime import datetime

import pytest

from app.models import Document, Reminder, Task, User
from app.services import paperless_service
from app.services.chatgpt_service import ChatGPTPermanentError
from app.tasks import calendar_sync as calendar_sync_module
from app.tasks import paperless_analyze

from .conftest import TestingSessionLocal

PAPERLESS_DOC = {
    "id": 4711,
    "title": "Zahlungserinnerung",
    "content": "Bitte zahlen Sie den offenen Betrag von 49,90 EUR bis zum 30.11.2026.",
    "created": "2026-10-23",
    "tags": [],
}

AI_RESULT = {
    "type": "Mahnung",
    "summary": "Offener Betrag 49,90 EUR",
    "tags": ["Mahnung"],
    "action_required": True,
    "sender": "Inkasso GmbH",
    "amount": 49.90,
    "currency": "EUR",
    "due_date": "2026-11-30",
}


@pytest.fixture()
def user(db):
    u = User(username="paperless", email="paperless@example.com", password_hash="x", fcm_token="fcm-123")
    db.add(u)
    db.commit()
    return u


class FakePaperlessClient:
    async def get_documents(self, created_after=None, page=1):
        return {"results": [PAPERLESS_DOC] if page == 1 else [], "next": None}


class TestImport:
    def test_analysis_is_dispatched_after_commit(self, db, user, monkeypatch):
        monkeypatch.setattr(paperless_service, "get_paperless_client", lambda *a, **k: FakePaperlessClient())
        calls = []
        original_commit = db.commit
        monkeypatch.setattr(db, "commit", lambda: (calls.append("commit"), original_commit())[1])
        monkeypatch.setattr(
            paperless_analyze.analyze_paperless_document, "delay", lambda document_id: calls.append("delay")
        )

        import asyncio
        result = asyncio.run(paperless_service.PaperlessSyncService(db, user.id).import_new_documents())

        # The worker reads the document in its own session — it must be committed before dispatch
        assert result == {"imported": 1, "skipped": 0}
        assert "delay" in calls
        assert calls.index("commit") < calls.index("delay"), f"analysis dispatched before commit: {calls}"
        assert db.query(Document).one().processing_status == "pending"

    def test_already_imported_document_is_skipped(self, db, user, monkeypatch):
        monkeypatch.setattr(paperless_service, "get_paperless_client", lambda *a, **k: FakePaperlessClient())
        monkeypatch.setattr(paperless_analyze.analyze_paperless_document, "delay", lambda *a, **k: None)

        import asyncio
        svc = paperless_service.PaperlessSyncService(db, user.id)
        asyncio.run(svc.import_new_documents())
        assert asyncio.run(svc.import_new_documents()) == {"imported": 0, "skipped": 1}


@pytest.fixture()
def pending_doc(db, user):
    doc = Document(
        user_id=user.id,
        type="other",
        title="Zahlungserinnerung",
        processing_status="pending",
        extracted_text=PAPERLESS_DOC["content"],
        doc_metadata={"source": "paperless_ngx"},
    )
    db.add(doc)
    db.commit()
    return doc


@pytest.fixture()
def analyze_env(monkeypatch):
    """Run the analysis task against the test DB with Claude and push mocked"""
    monkeypatch.setattr(paperless_analyze, "SessionLocal", TestingSessionLocal)
    # The real constructor requires CLAUDE_API_KEY (not set in CI); analyze_for_paperless is mocked per test
    monkeypatch.setattr(paperless_analyze.ClaudeService, "__init__", lambda self: None)
    pushes = []

    from app.services import push_notification_service
    monkeypatch.setattr(
        push_notification_service.PushNotificationService, "send",
        lambda self, **kwargs: pushes.append(kwargs),
    )
    return pushes


class TestAnalysis:
    def test_analysis_sends_push_by_default(self, db, pending_doc, analyze_env, monkeypatch):
        monkeypatch.setattr(paperless_analyze.ClaudeService, "analyze_for_paperless", lambda self, text: AI_RESULT)

        paperless_analyze.analyze_paperless_document(str(pending_doc.id))

        db.expire_all()
        assert db.get(Document, pending_doc.id).processing_status == "done"
        assert len(analyze_env) == 1

    def test_notify_false_skips_push_but_creates_task(self, db, pending_doc, analyze_env, monkeypatch):
        monkeypatch.setattr(paperless_analyze.ClaudeService, "analyze_for_paperless", lambda self, text: AI_RESULT)

        paperless_analyze.analyze_paperless_document(str(pending_doc.id), notify=False)

        db.expire_all()
        doc = db.get(Document, pending_doc.id)
        assert doc.processing_status == "done"
        assert doc.doc_metadata["ai_summary"] == "Offener Betrag 49,90 EUR"
        assert analyze_env == []
        assert db.query(Task).filter(Task.document_id == doc.id).count() == 1

    def test_failure_stores_error_on_document(self, db, pending_doc, analyze_env, monkeypatch):
        def boom(self, text):
            raise RuntimeError("Claude API: credit balance too low")

        monkeypatch.setattr(paperless_analyze.ClaudeService, "analyze_for_paperless", boom)

        with pytest.raises(RuntimeError):
            paperless_analyze.analyze_paperless_document(str(pending_doc.id))

        db.expire_all()
        doc = db.get(Document, pending_doc.id)
        assert doc.processing_status == "failed"
        assert doc.doc_metadata["ai_error"] == "RuntimeError: Claude API: credit balance too low"


    def test_permanent_llm_error_is_not_retried(self, db, pending_doc, analyze_env, monkeypatch):
        def limit_reached(self, text):
            raise ChatGPTPermanentError("code=subscription_sharing_usage_limit_exceeded")

        retries = []
        monkeypatch.setattr(paperless_analyze.ClaudeService, "analyze_for_paperless", limit_reached)
        monkeypatch.setattr(
            paperless_analyze.analyze_paperless_document, "retry", lambda **kwargs: retries.append(kwargs)
        )

        with pytest.raises(ChatGPTPermanentError):
            paperless_analyze.analyze_paperless_document(str(pending_doc.id))

        assert retries == []
        db.expire_all()
        assert db.get(Document, pending_doc.id).processing_status == "failed"


class TestCalendarSyncTask:
    def test_runs_without_integrations(self, db, monkeypatch):
        # Used to crash with AttributeError: Integration has no attribute 'is_active'
        monkeypatch.setattr(calendar_sync_module, "SessionLocal", TestingSessionLocal)
        # independent of a local .env (the dev instance has CALENDAR_SYNC_ENABLED=false)
        monkeypatch.setattr(calendar_sync_module.settings, "CALENDAR_SYNC_ENABLED", True)
        assert calendar_sync_module.calendar_sync() == {"synced": 0}


class TestOverdueReminderTime:
    """Overdue reminders go out the next morning at 08:00 local time, not right away"""

    @pytest.mark.parametrize(
        "now_utc, timezone, expected_utc",
        [
            # 19:30 CEST -> next day 08:00 CEST
            (datetime(2026, 10, 23, 17, 30), "UTC", datetime(2026, 10, 24, 6, 0)),
            # 06:00 CEST -> 08:00 the same day
            (datetime(2026, 10, 24, 4, 0), None, datetime(2026, 10, 24, 6, 0)),
            # exactly 08:00 -> the next day
            (datetime(2026, 10, 24, 6, 0), None, datetime(2026, 10, 25, 7, 0)),
            # DST ends on 25.10. -> 08:00 CET is 07:00 UTC
            (datetime(2026, 10, 24, 20, 0), "Europe/Berlin", datetime(2026, 10, 25, 7, 0)),
            # winter time
            (datetime(2026, 11, 10, 20, 0), "Europe/Berlin", datetime(2026, 11, 11, 7, 0)),
            # explicit other timezone is respected
            (datetime(2026, 10, 23, 17, 30), "America/New_York", datetime(2026, 10, 24, 12, 0)),
            # unknown timezone falls back to Europe/Berlin
            (datetime(2026, 10, 23, 17, 30), "Mars/Olympus", datetime(2026, 10, 24, 6, 0)),
        ],
    )
    def test_next_morning(self, now_utc, timezone, expected_utc):
        assert paperless_analyze._next_morning_utc(now_utc, timezone) == expected_utc

    def test_overdue_document_reminder_is_next_morning(self, db, pending_doc, analyze_env, monkeypatch):
        overdue = {**AI_RESULT, "due_date": "2026-01-15"}
        monkeypatch.setattr(paperless_analyze.ClaudeService, "analyze_for_paperless", lambda self, text: overdue)

        paperless_analyze.analyze_paperless_document(str(pending_doc.id), notify=False)

        reminder = db.query(Reminder).one()
        assert reminder.trigger_at == paperless_analyze._next_morning_utc(datetime.utcnow(), "UTC")


class WritebackClient:
    """Minimal stand-in for PaperlessClient that records the PATCH"""

    def __init__(self, current):
        self.current = current
        self.patched = None
        self.created = []
        self._ids = iter(range(900, 999))

    async def get_document(self, document_id):
        return self.current

    async def _get_or_create(self, kind, name):
        self.created.append((kind, name))
        return {"id": next(self._ids), "name": name}

    async def get_or_create_tag(self, name):
        return await self._get_or_create("tag", name)

    async def get_or_create_correspondent(self, name):
        return await self._get_or_create("correspondent", name)

    async def get_or_create_document_type(self, name):
        return await self._get_or_create("document_type", name)

    async def update_document(self, document_id, **kwargs):
        self.patched = kwargs


WRITEBACK_RESULT = {
    "type": "Rechnung", "sender": "Matenaar Service GmbH", "summary": "Lohnabrechnung",
    "tags": ["Lohn"], "amount": "1906.95", "due_date": None,
}


class TestWriteToPaperless:
    def _run(self, monkeypatch, current):
        import asyncio
        from app.tasks import paperless_analyze

        fake = WritebackClient(current)
        monkeypatch.setattr(paperless_analyze, "get_paperless_client", lambda: fake)
        asyncio.run(paperless_analyze._write_to_paperless(568, dict(WRITEBACK_RESULT)))
        return fake

    def test_curated_document_keeps_title_tags_correspondent_and_type(self, monkeypatch):
        fake = self._run(monkeypatch, {
            "title": "Matenaar Lohnabrechnung April 2026", "tags": [54, 160],
            "correspondent": 45, "document_type": 5,
        })
        assert fake.patched["tags"][:2] == [54, 160]
        assert len(fake.patched["tags"]) == 3
        assert fake.patched["title"] is None
        assert fake.patched["correspondent"] is None
        assert fake.patched["document_type"] is None
        assert ("correspondent", "Matenaar Service GmbH") not in fake.created

    def test_fresh_scan_gets_title_correspondent_and_type(self, monkeypatch):
        fake = self._run(monkeypatch, {
            "title": "Scan_08112026165306_20261108165306", "tags": [],
            "correspondent": None, "document_type": None,
        })
        assert fake.patched["title"].startswith("Matenaar Service GmbH – Rechnung")
        assert fake.patched["correspondent"] is not None
        assert fake.patched["document_type"] is not None
        assert len(fake.patched["tags"]) == 1

    @pytest.mark.parametrize("title,expected", [
        ("Scan_08112026163907_20261108163907", True),
        ("Scan 15.11.2019", True),
        ("", True),
        ("Experis Arbeitszeugnis", False),
        ("Scanner-Handbuch Xerox", False),
    ])
    def test_default_title_detection(self, title, expected):
        from app.tasks.paperless_analyze import _is_default_title
        assert _is_default_title(title) is expected


def test_get_or_create_tag_finds_tag_on_second_page(monkeypatch):
    """Paperless hat mehr als 100 Tags: Tag auf Seite 2 darf nicht neu angelegt werden (400 Duplicate)"""
    import asyncio
    from app.services.paperless_service import PaperlessClient

    client = PaperlessClient("https://paperless.test", "token")
    pages = {
        1: {"results": [{"id": i, "name": f"tag{i}"} for i in range(100)], "next": "page=2"},
        2: {"results": [{"id": 160, "name": "Steuer 2025"}], "next": None},
    }

    async def fake_get(endpoint, params=None):
        return pages[params["page"]]

    async def fail_post(endpoint, data):
        raise AssertionError("darf keinen Tag anlegen")

    monkeypatch.setattr(client, "_get", fake_get)
    monkeypatch.setattr(client, "_post", fail_post)
    tag = asyncio.run(client.get_or_create_tag("steuer 2025"))
    assert tag["id"] == 160
