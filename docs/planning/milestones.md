# Meilensteine

## Übersicht

Dieses Dokument verfolgt konkrete Meilensteine mit spezifischen Ergebnissen und Terminen.

---

## Meilenstein 0: Dokumentation abgeschlossen ✅

**Status:** In Bearbeitung (95%)
**Ziel:** Januar 2026
**Erreicht:** 19. Januar 2026

**Ergebnisse:**
- [x] README.md
- [x] docs/concept/ (3 Dateien)
- [x] docs/architecture/ (4 Dateien)
- [x] docs/features/ (7 Dateien)
- [x] docs/development/ (4 Dateien)
- [x] docs/planning/ (3 Dateien)
- [x] CONTRIBUTING.md

**Ergebnis:** Vollständige Projektdokumentation bereit für Entwicklungsstart.

---

## Meilenstein 1: Repository-Setup

**Status:** Teilweise (lokales Repo vorhanden, GitHub noch nicht public)
**Ziel:** Januar 2026 → verschoben
**Verantwortlich:** Joshua

**Aufgaben:**
- [ ] GitHub-Repository erstellen (öffentlich)
- [x] Initiale Code-Struktur (lokal vorhanden, git history seit Jan 2026)
- [ ] GitHub Actions einrichten (CI/CD)
- [ ] Branch-Schutz konfigurieren
- [ ] Issue-Templates erstellen
- [ ] Projekt-Board einrichten

**Akzeptanzkriterien:**
- Repository erreichbar unter github.com/commanderphu/workmate-private
- CI läuft bei jedem PR (Linting, Tests)
- Contributing-Richtlinien sichtbar

---

## Meilenstein 2: Backend-Grundlage

**Status:** ✅ ABGESCHLOSSEN (Januar 2026)
**Ziel:** Februar 2026 → früher fertig
**Verantwortlich:** Joshua

**Aufgaben:**
- [x] FastAPI-Projektstruktur
- [x] Datenbankmodelle (SQLAlchemy) – User, Document, Task, File, Reminder, Session, CalendarEvent, Integration
- [x] Alembic-Migrationen einrichten (2 Migrationen)
- [x] Basis-Authentifizierung (JWT + Argon2)
- [x] Benutzer-CRUD-Endpunkte
- [x] Health-Check-Endpunkt (+ HTML-Dashboard unter `/health/ui`)
- [x] Docker-Setup (PostgreSQL, Redis, Backend, Celery)
- [ ] Unit-Tests (>70% Abdeckung) – ausstehend

**Akzeptanzkriterien:**
- [x] `/health` gibt 200 zurück
- [x] Benutzerregistrierung & Login funktioniert
- [ ] Tests bestehen
- [x] Läuft in Docker

**Geschätzter Aufwand:** 40 Stunden

---

## Meilenstein 3: Frontend-Grundlage

**Status:** ✅ ABGESCHLOSSEN (Januar - April 2026)
**Ziel:** Februar 2026 → erweitert fertig
**Verantwortlich:** Joshua

**Aufgaben:**
- [x] Flutter-Projektstruktur
- [x] Login-/Registrierungs-Bildschirme
- [x] Navigation (Drawer)
- [x] API-Client (api_service.dart + auth_service.dart)
- [x] State-Management (Provider)
- [x] Theme & Design-System (Dark Mode, Accent Color, SharedPreferences)
- [x] Alle Haupt-Pages: Dashboard, Tasks, Documents, Calendar, Integrations, Settings

**Akzeptanzkriterien:**
- [x] Login-Flow implementiert
- [x] ADHD-freundliche UI
- [x] Funktioniert auf Web & Android

**Geschätzter Aufwand:** 30 Stunden

---

## Meilenstein 4: Dokumentenverarbeitung MVP

**Status:** ✅ ABGESCHLOSSEN (März - April 2026)
**Ziel:** März 2026
**Verantwortlich:** Joshua

**Aufgaben:**
- [x] Datei-Upload-Endpunkt (`/api/v1/documents/`)
- [x] Speicherdienst (lokal – `file_storage.py`)
- [x] OCR-Integration (Tesseract via `ocr_service.py`)
- [x] Claude-API-Integration (`claude_service.py`)
- [x] Dokumentenklassifizierung (via Claude)
- [x] Metadaten-Extraktion (Betrag, Fälligkeitsdatum, Sender, etc.)
- [x] Frontend-Upload-UI (Web + Mobile, `file_upload_service_web/mobile`)
- [x] Verarbeitungsstatus-Anzeige (`document_detail_page.dart`)
- [x] Async Processing via Celery (`document_processing.py`)

**Akzeptanzkriterien:**
- [x] Upload PDF/Bild → verarbeitet (Async via Celery)
- [x] KI-Klassifizierung mit Claude
- [x] Extrahierte Metadaten in UI sichtbar

**Geschätzter Aufwand:** 50 Stunden

---

## Meilenstein 5: Aufgabenverwaltung MVP

**Status:** ✅ ABGESCHLOSSEN (Januar - März 2026)
**Ziel:** März 2026
**Verantwortlich:** Joshua

**Aufgaben:**
- [x] Aufgabenmodell & Endpunkte (`/api/v1/tasks/`)
- [x] CRUD-Operationen (GET, POST, PATCH, DELETE)
- [x] Automatische Aufgabenerstellung aus Dokumenten (via Claude-Analyse)
- [x] Frontend-Aufgabenliste (`tasks_page.dart`)
- [x] Aufgabendetail-Ansicht (`task_detail_page.dart`)
- [x] Als-erledigt-markieren
- [x] Status & Priorität (open, in_progress, done, cancelled / low, medium, high, critical)

**Akzeptanzkriterien:**
- [x] Tasks CRUD funktioniert
- [x] Benutzer kann Aufgaben ansehen, bearbeiten, abschließen

**Geschätzter Aufwand:** 40 Stunden

---

## Meilenstein 6: Erinnerungs-Engine MVP

**Status:** 🟡 IN ARBEIT (April 2026)
**Ziel:** April 2026
**Verantwortlich:** Joshua

**Aufgaben:**
- [x] Celery-Setup (Worker + Beat in docker-compose)
- [x] Erinnerungsmodell (`reminder.py` – Multi-Stage: info, warning, urgent, critical)
- [x] Planungslogik (`reminder_service.py`)
- [x] Push-Benachrichtigungsdienst – Firebase FCM (`push_notification_service.py`)
- [x] FCM-Token Registration API (`/api/v1/notifications/fcm-token`)
- [x] Celery-Dispatch-Task (`tasks/reminder_dispatch.py` – alle 60s)
- [ ] E-Mail-Benachrichtigungsdienst – **ausstehend**
- [x] Erinnerungsgenerierung aus Aufgaben (via reminder_service)
- [ ] Frontend-Benachrichtigungseinstellungen
- [ ] End-to-End-Test mit echten Aufgaben – **ausstehend**

**Akzeptanzkriterien:**
- 🟡 Erinnerungen implementiert, End-to-End-Test ausstehend
- ✅ Push-Benachrichtigungen implementiert (Firebase FCM)
- ❌ E-Mail-Benachrichtigungen noch nicht implementiert

**Geschätzter Aufwand:** 60 Stunden

---

## Meilenstein 7: Beta-Release 🎉

**Status:** ✅ ABGESCHLOSSEN – April 2026 (1 Monat vor Plan!)
**Ziel:** Mai 2026 → April 2026 erreicht
**Verantwortlich:** Joshua

**Aufgaben:**
- [x] Hetzner cax11 Server (ARM64, 2vCPU, 4GB) aufgesetzt
- [x] SSL-Setup (Let's Encrypt via Certbot)
- [x] Domain: workmate-private.phudevelopement.xyz
- [x] Docker Compose Production Config
- [x] GitHub Actions CI/CD (ARM64 Build + Deploy)
- [x] Discord Deploy Notifications
- [x] Firebase App Distribution (APK-Verteilung)
- [x] Erster User angelegt (Joshua)
- [ ] Onboarding-Flow – ausstehend
- [ ] 5-10 Beta-Benutzer rekrutieren

**Akzeptanzkriterien:**
- [x] Erreichbar unter workmate-private.phudevelopement.xyz
- [x] SSL aktiv
- [x] APK via Firebase App Distribution installierbar
- [ ] 5+ aktive Beta-Benutzer (aktuell: 1)

**Beta-Tester:**
1. Joshua ✅ (aktiv)
2. TBD
3. TBD
4. TBD
5. TBD

---

## Meilenstein 8: Kalender-Integration

**Status:** ✅ ABGESCHLOSSEN – vorgezogen auf April 2026
**Ziel:** Juni 2026 → früher fertig
**Verantwortlich:** Joshua

**Aufgaben:**
- [x] CalDAV-Implementierung (`caldav_service.py`)
- [x] Google Calendar OAuth2 (`google_calendar_service.py`)
- [x] Sync-Dienst (`calendar_sync_service.py`)
- [x] Bidirektionale Sync-Logik (Push + Pull)
- [x] Konfliktauflösung (conflict_data JSONB, ConflictResolution)
- [x] Task → CalendarEvent Mapping (`task_event_mapping_service.py`)
- [x] Frontend-Integrations-Setup-UI (`integrations_page.dart`, `integration_setup_dialog.dart`)
- [x] Kalender-API Endpoints (`/api/v1/calendar`)
- [ ] Tests mit mehreren Kalendern – ausstehend
- [ ] Microsoft Outlook – noch nicht implementiert

**Akzeptanzkriterien:**
- [x] Tasks synchronisieren zu CalDAV & Google Calendar
- [x] Bidirektionaler Sync-Service vorhanden
- [x] Konfliktdaten werden gespeichert
- [ ] Outlook noch offen

**Geschätzter Aufwand:** 50 Stunden

---

## Meilenstein 9: Erweiterte Funktionen

**Status:** Nicht begonnen
**Ziel:** Juli - September 2026
**Verantwortlich:** Joshua

**Zu implementierende Funktionen:**
- [ ] Unteraufgaben & Abhängigkeiten
- [ ] Wiederkehrende Aufgaben
- [ ] Suche & Filter
- [ ] Tag-System
- [ ] Analyse-Dashboard
- [ ] Paperless-ngx-Integration
- [ ] Smart Home (Home Assistant)

**Akzeptanzkriterien:**
- Alle Funktionen von Beta-Benutzern getestet
- Dokumentation aktualisiert
- Keine Regressionen

**Geschätzter Aufwand:** 120 Stunden

---

## Meilenstein 10: Öffentliche Beta

**Status:** Nicht begonnen
**Ziel:** September 2026
**Verantwortlich:** Joshua

**Aufgaben:**
- [ ] Performance-Optimierung
- [ ] Sicherheitsaudit
- [ ] UI/UX-Verfeinerung
- [ ] Mobile-App (Android) veröffentlicht
- [ ] Öffentliche Ankündigung
- [ ] Auf 50+ Benutzer erweitern
- [ ] Community-Setup (Discord?)

**Akzeptanzkriterien:**
- 50+ aktive Benutzer
- <5s durchschnittliche Antwortzeit
- >85% Benutzerzufriedenheit
- App im Google Play Store

---

## Meilenstein 11: v1.0 Release 🚀

**Status:** Nicht begonnen
**Ziel:** Dezember 2026
**Verantwortlich:** Joshua

**Aufgaben:**
- [ ] Feature-Freeze
- [ ] Vollständige Test-Abdeckung (>80%)
- [ ] Benutzerdokumentation vollständig
- [ ] Migrations-Anleitungen
- [ ] Release-Notes
- [ ] Marketing-Materialien
- [ ] Pressemitteilung (optional)

**Akzeptanzkriterien:**
- Alle Phase-3-Funktionen implementiert
- Stabil, produktionsreif
- 200+ aktive Benutzer (Ziel)
- Community etabliert

---

## Meilenstein 12: K.I.T. Entscheidungspunkt

**Status:** Nicht begonnen
**Ziel:** November 2026
**Verantwortlich:** Joshua

**Entscheidung:** Vollzeit mit K.I.T. Solutions?

**Bewertungskriterien:**
- [ ] 200+ aktive Workmate-Benutzer
- [ ] 80%+ Benutzerzufriedenheit
- [ ] Nachhaltige Einnahmen (falls monetarisiert)
- [ ] Persönliches Wohlbefinden prüfen
- [ ] Unterstützung der Partnerin (Jessica)

**Ergebnisse:**
- **Los:** 100% Fokus auf K.I.T., beschleunigte Entwicklung
- **Warten:** Teilzeit fortsetzen, in 6 Monaten neu bewerten

**Das ist der GROSSE Meilenstein!**

---

## Timeline-Visualisierung
```
2026
├── Q1: Grundlage ✅
│   ├── Jan: Dokumentation ✅
│   ├── Jan: Backend Grundlage ✅ (früher als geplant)
│   └── Jan-Mär: Dokumentenverarbeitung + Aufgaben MVP ✅
│
├── Q2: MVP 🟡 (aktuell)
│   ├── Apr: Erinnerungen MVP 🟡 (Kern fertig, Push/Email offen)
│   ├── Apr: Kalender-Integration ✅ (vorgezogen aus Q3!)
│   ├── Mai: Beta Release 🎯 ← NÄCHSTES ZIEL
│   │       (Push Notifications + Deployment nötig)
│   └── Jun: [Puffer / CI/CD / GitHub Public]
│
├── Q3: Erweiterung
│   ├── Jul: Sub-Tasks, Recurring Tasks, Search
│   ├── Aug: Paperless-ngx, Analytics
│   └── Sep: Öffentliche Beta
│
└── Q4: Intelligente Funktionen
    ├── Okt: Smart Home, KI-Verbesserungen
    ├── Nov: K.I.T. Entscheidungspunkt ⚡
    └── Dez: v1.0 Release 🚀
```

---

## Nachverfolgung

**Status-Updates:** Alle 2 Wochen
**Review:** Monatlich
**Ort:** GitHub-Projekt-Board

**Fortschrittsmetriken:**
- Abgeschlossene Meilensteine: 7/12 (58%) – M0, M2, M3, M4, M5, M7, M8
- In Arbeit: 1/12 – M6 (Reminder Engine – Push ✅, Email offen)
- Offen: 4/12 – M1, M9, M10, M11, M12
- Geschätzter Gesamtaufwand: ~450 Stunden
- Stand: April 2026 – deutlich vor Plan, Beta bereits live!

---

## Notizen

- Zeitpläne sind Schätzungen, Flexibilität ist wichtig
- ADHD-freundlich: Kein Druck, Fortschritt vor Perfektion
- Beta-Feedback wird Prioritäten beeinflussen
- Einige Meilensteine können sich basierend auf Erkenntnissen verschieben
