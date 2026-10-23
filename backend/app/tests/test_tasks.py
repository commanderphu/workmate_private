"""
Tests for the task API: CRUD, validation, user isolation, calendar event mapping
"""

from datetime import datetime, timedelta

from app.models import CalendarEvent

TASKS = "/api/v1/tasks/"


def create_task(client, headers, **fields):
    payload = {"title": "Steuererklärung abgeben", **fields}
    response = client.post(TASKS, json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


class TestCreate:
    def test_create_with_defaults(self, client, auth_headers):
        task = create_task(client, auth_headers)
        assert task["title"] == "Steuererklärung abgeben"
        assert task["status"] == "open"
        assert task["priority"] == "medium"
        assert task["currency"] == "EUR"
        assert task["completed_at"] is None

    def test_create_with_amount_and_priority(self, client, auth_headers):
        task = create_task(client, auth_headers, priority="critical", amount="49.90")
        assert task["priority"] == "critical"
        assert float(task["amount"]) == 49.90

    def test_invalid_priority_is_rejected(self, client, auth_headers):
        response = client.post(TASKS, json={"title": "x", "priority": "dringend"}, headers=auth_headers)
        assert response.status_code == 422

    def test_empty_title_is_rejected(self, client, auth_headers):
        response = client.post(TASKS, json={"title": ""}, headers=auth_headers)
        assert response.status_code == 422

    def test_requires_authentication(self, client):
        assert client.post(TASKS, json={"title": "x"}).status_code == 401
        assert client.get(TASKS).status_code == 401


class TestReadAndIsolation:
    def test_list_returns_own_tasks(self, client, auth_headers):
        create_task(client, auth_headers, title="A")
        create_task(client, auth_headers, title="B")
        titles = {t["title"] for t in client.get(TASKS, headers=auth_headers).json()}
        assert titles == {"A", "B"}

    def test_other_user_sees_nothing(self, client, auth_headers, other_auth_headers):
        task = create_task(client, auth_headers)
        assert client.get(TASKS, headers=other_auth_headers).json() == []
        assert client.get(f"{TASKS}{task['id']}", headers=other_auth_headers).status_code == 404

    def test_other_user_cannot_update_or_delete(self, client, auth_headers, other_auth_headers):
        task = create_task(client, auth_headers)
        url = f"{TASKS}{task['id']}"
        assert client.patch(url, json={"title": "gekapert"}, headers=other_auth_headers).status_code == 404
        assert client.delete(url, headers=other_auth_headers).status_code == 404
        assert client.get(url, headers=auth_headers).json()["title"] == task["title"]

    def test_status_filter(self, client, auth_headers):
        done = create_task(client, auth_headers, title="erledigt")
        create_task(client, auth_headers, title="offen")
        client.patch(f"{TASKS}{done['id']}", json={"status": "done"}, headers=auth_headers)

        result = client.get(TASKS, params={"status_filter": "done"}, headers=auth_headers).json()
        assert [t["title"] for t in result] == ["erledigt"]


class TestUpdate:
    def test_done_sets_completed_at(self, client, auth_headers):
        task = create_task(client, auth_headers)
        updated = client.patch(f"{TASKS}{task['id']}", json={"status": "done"}, headers=auth_headers).json()
        assert updated["status"] == "done"
        assert updated["completed_at"] is not None

    def test_reopen_clears_completed_at(self, client, auth_headers):
        task = create_task(client, auth_headers)
        url = f"{TASKS}{task['id']}"
        client.patch(url, json={"status": "done"}, headers=auth_headers)
        reopened = client.patch(url, json={"status": "open"}, headers=auth_headers).json()
        assert reopened["completed_at"] is None

    def test_invalid_status_is_rejected(self, client, auth_headers):
        task = create_task(client, auth_headers)
        response = client.patch(f"{TASKS}{task['id']}", json={"status": "fertig"}, headers=auth_headers)
        assert response.status_code == 422

    def test_partial_update_keeps_other_fields(self, client, auth_headers):
        task = create_task(client, auth_headers, priority="high", description="Belege sammeln")
        updated = client.patch(f"{TASKS}{task['id']}", json={"title": "Neu"}, headers=auth_headers).json()
        assert updated["title"] == "Neu"
        assert updated["priority"] == "high"
        assert updated["description"] == "Belege sammeln"


class TestDelete:
    def test_delete(self, client, auth_headers):
        task = create_task(client, auth_headers)
        url = f"{TASKS}{task['id']}"
        assert client.delete(url, headers=auth_headers).status_code == 204
        assert client.get(url, headers=auth_headers).status_code == 404

    def test_unknown_task_is_404(self, client, auth_headers):
        url = f"{TASKS}00000000-0000-0000-0000-000000000000"
        assert client.get(url, headers=auth_headers).status_code == 404


class TestCalendarEventMapping:
    def test_due_date_creates_calendar_event(self, client, auth_headers, db):
        due = (datetime.utcnow() + timedelta(days=5)).replace(microsecond=0)
        task = create_task(client, auth_headers, priority="critical", due_date=due.isoformat())

        events = db.query(CalendarEvent).all()
        assert len(events) == 1
        event = events[0]
        assert str(event.task_id) == task["id"]
        assert event.title == "🔴 Steuererklärung abgeben"
        assert event.end_time == due
        assert event.start_time == due - timedelta(hours=1)

    def test_task_without_due_date_has_no_event(self, client, auth_headers, db):
        create_task(client, auth_headers)
        assert db.query(CalendarEvent).count() == 0

    def test_removing_due_date_deletes_event(self, client, auth_headers, db):
        due = (datetime.utcnow() + timedelta(days=5)).replace(microsecond=0)
        task = create_task(client, auth_headers, due_date=due.isoformat())
        assert db.query(CalendarEvent).count() == 1

        client.patch(f"{TASKS}{task['id']}", json={"due_date": None}, headers=auth_headers)
        assert db.query(CalendarEvent).count() == 0
