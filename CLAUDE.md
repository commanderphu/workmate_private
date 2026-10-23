# Workmate Private

Persönliches ADHD-Taskmanagement + Paperless-Integration. Hetzner cax11 (ARM64, 178.104.207.155), URL: `https://workmate-private.phudevelopement.xyz`, SSH: `ssh workmate@178.104.207.155`.

## Stack

- **Backend:** FastAPI + PostgreSQL + Celery + Redis (Python 3.13)
- **Frontend:** Flutter Web + Android (`xyz.phudevelopement.workmate_private`)
- **Compose:** `docker-compose.prod.yml`, Deploy via GitHub Actions (~20 Min ARM64-Build)

## Auth

- JWT (30 Min) + Refresh Token (7 Tage), kein Keycloak
- Permanent API-Key: `X-API-Key` Header (in `.env` als `WORKMATE_API_TOKEN`)
- Refresh-Endpoint: `POST /api/v1/auth/refresh`

## Wichtige Pfade

- Backend: `backend/app/`
- Migrations: `backend/migrations/versions/`
- Flutter: `frontend/lib/`
- Android Keystore: `frontend/android/app/workmate-release.jks`

## Lokales Dev-Tooling

- **Steuerung über `Makefile`** im Repo-Root (`make help`): Container (`up`, `recreate`, `restart-workers`, `logs`), DB (`backup`, `migrate` = Backup + `alembic upgrade head`, `db-current`), Tooling (`venv`, `lint`, `test`, `pre-commit`)
- venv im Repo-Root (`venv/`, Python 3.13 wie im Docker-Image, angelegt mit `uv`; System-Python ist 3.14 und hat keine Wheels für die gepinnten Pakete): `~/.local/share/uv-bootstrap/bin/uv pip install -r backend/requirements.txt -r backend/requirements-dev.txt` (mit `VIRTUAL_ENV=$PWD/venv`)
- pre-commit (`.pre-commit-config.yaml`): flake8 mit denselben harten Regeln wie die Backend-CI (`E9,F63,F7,F82`) + Basis-Checks; black bewusst noch nicht (würde 50 Dateien umformatieren)
- Dev-Backend läuft mit `--reload --reload-dir app` — Code-Änderungen ohne Container-Neustart; Celery-Worker/Beat brauchen weiterhin `docker restart`

## APK bauen (lokal)

```bash
cd /mnt/data/docs/Dokumente/Projekts/PhuDev/workmate_private/frontend
export WORKMATE_KEYSTORE_PASS=$(cat ~/.credentials/.workmate_keystore_pass)
flutter build apk --release
adb install -r build/app/outputs/flutter-apk/app-release.apk
```

## Paperless-Integration

- Paperless auf Gideon: `https://office.phudevelopement.xyz`, Token in Bitwarden
- Celery-Beat synct alle 30 Min (`paperless_sync`), Parameter: `added__date__gte`
- Claude AI analysiert Dokumente → Task + CalendarEvent + Reminder automatisch
- E-Mail-Import läuft bei Paperless-ngx selbst (IMAP, 3 Konten) — Workmate braucht/hat keinen eigenen IMAP-Client, bekommt solche Dokumente automatisch über `paperless_sync` mit
- Sync ist aktuell einseitig (Paperless → Workmate) + einmaliger Tag-Write-back nach KI-Analyse; laufender bidirektionaler Sync ist offen (Issue #1)

## Offene Aufgaben

Werden als GitHub Issues im Repo getrackt, nicht in Doku-Dateien dupliziert:

```bash
gh issue list --repo commanderphu/workmate_private
```

## Google Calendar

- Integration via OAuth, Kalender: `callmephu95@gmail.com` (primär) + Work & Study, Events, Freunde/Familie, Gesundheit
- Sync alle 15 Min bidirektional, Endpoint: `/api/v1/calendar/events/?start_date=...&end_date=...`

## Reminder Engine & Push

- Reminder-Schedule ist prioritätsabhängig (`backend/app/services/reminder_service.py`, `REMINDER_SCHEDULE`): critical 0/1/3, high 0/2/7, medium 0/3, low 0 Tage vor Fälligkeit (abgesichert durch `backend/app/tests/test_reminder_schedule.py`); Verträge (`CONTRACT_REMINDER_SCHEDULE`) 30/14/7/1 Tag vor Kündigungsfrist
- Push via Firebase Cloud Messaging (`push_notification_service.py`), FCM-Token via `POST/DELETE /api/v1/notifications/fcm-token`
- `FIREBASE_CREDENTIALS_PATH` muss auf eine existierende Datei zeigen, sonst startet der Container nicht (in `docker-compose.prod.yml` fest gemountet als `./firebase-credentials.json`) — ohne echtes Firebase-Projekt reicht eine leere `{}`-Datei, Push bleibt dann nur deaktiviert (Log-Warnung, kein Crash)

## Celery-Beat-Tasks (`backend/app/celery.py`)

| Task-Name | Intervall |
|---|---|
| `app.tasks.dispatch_reminders` | 60s |
| `app.tasks.paperless_sync` | 30 Min |
| `app.tasks.calendar_sync` | 15 Min |

`app.tasks.process_document` (Upload-Pipeline) und `app.tasks.analyze_paperless_document` laufen nicht periodisch, sondern werden pro Dokument angestoßen.

## Bekannte Fallstricke

- Postgres-User: `workmate_private`, DB: `workmate_private` (nicht `workmate`)
- Celery Task-Name: `app.tasks.paperless_sync` (nicht `.sync_paperless_documents`)
- `added__date__gte` statt `created__date__gte` für Paperless-Sync
- GitHub Actions APK-Build schlägt fehl (Keystore fehlt in CI) — lokal bauen
- Root-`docker-compose.yml` ist Joshuas persönliches Dev-Setup (kein Postgres-Service, keine Port-Mappings, setzt externes Docker-Netzwerk `core_network` + zentralen Postgres-Host voraus) — für eigenständiges Self-Hosting `docker-compose.prod.yml` verwenden
- Dev-Instanz (Root-Compose auf cisco) hängt am selben Paperless + Google-Kalender wie Prod → dort `PAPERLESS_SYNC_ENABLED=false` und `CALENDAR_SYNC_ENABLED=false` in `.env` (Default `true`); `.env`-Änderungen brauchen `docker compose up -d --force-recreate`, kein bloßes Restart
- Prod-nginx löst den Backend-Namen nur beim Start auf: Wird das Backend neu erstellt (Deploy, Teil-Neustart), gibt es 502 auf die alte IP → `docker compose -f docker-compose.prod.yml restart nginx` (macht der Deploy-Workflow seit 23.10.2026 automatisch)
- `files.py`-Router hängt nicht unter `/api/v1`, sondern direkt unter `/files` (siehe `main.py`)
