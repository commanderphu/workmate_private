"""
Tests for the Paperless import -> AI analysis pipeline and the periodic calendar sync
"""

import pytest

from app.models import Document, Task, User
from app.services import paperless_service
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


class TestCalendarSyncTask:
    def test_runs_without_integrations(self, db, monkeypatch):
        # Used to crash with AttributeError: Integration has no attribute 'is_active'
        monkeypatch.setattr(calendar_sync_module, "SessionLocal", TestingSessionLocal)
        assert calendar_sync_module.calendar_sync() == {"synced": 0}
