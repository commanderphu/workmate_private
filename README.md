# Workmate Private

> **Dein digitaler Arbeitskollege. Von einem Neurodivergenten für die Neurodivergenten.**

![Status: Live](https://img.shields.io/badge/status-live-brightgreen)
![License: MIT](https://img.shields.io/badge/license-MIT-blue)
![Made with ❤️ for ADHD](https://img.shields.io/badge/made%20with%20%E2%9D%A4%EF%B8%8F%20for-ADHD-ff69b4)
![Flutter](https://img.shields.io/badge/Flutter-Android%20%7C%20Web-02569B)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)

## 🎯 Was ist Workmate Private?

Ein intelligentes Organisationssystem, das speziell für Menschen mit ADHD entwickelt wurde. Workmate Private hilft dabei, keine Rechnungen mehr zu vergessen, keine Fristen zu verpassen und den Papierkram endlich in den Griff zu bekommen – ohne dass du dich selbst „zusammenreißen" musst.

Einfach Dokument scannen → KI analysiert → Task wird erstellt → Erinnerung kommt rechtzeitig.

## 💡 Die Idee dahinter

Die Welt wurde von und für neurotypische Menschen designt. Bürokratie, Dokumenten-Management, Fristen – alles Systeme, die uns Neurodivergente systematisch benachteiligen.

**Warum sollten wir uns ständig anpassen, wenn wir auch Systeme bauen können, die mit unserem Gehirn funktionieren statt dagegen?**

Workmate Private ist die Antwort darauf: Ein Tool, das nicht versucht, dich zu „reparieren", sondern dich enablet.

## ✨ Features

### 📄 Intelligente Dokumenten-Erkennung
- Scan direkt per Handy-Kamera oder Datei-Upload
- **10 Dokumententypen** werden automatisch erkannt:

| Typ | Beschreibung |
|-----|-------------|
| Rechnung | Automatisch bezahlen / als Task anlegen |
| Mahnung | Sofort-Eskalation, kritische Erinnerung |
| Vertrag | Kündigungsfrist extrahieren, Ablauf-Reminder |
| Quittung | Archivierung |
| Steuerdokument | Lohnsteuerbescheinigung, Steuerbescheid |
| Gehaltsabrechnung | Archivierung & Ablage |
| Versicherung | Police, Schadensmeldungen |
| Kontoauszug | Archivierung |
| Brief / Behörde | Behördenpost, sonstige Post |
| Ausweis / Pass | Ablaufdatum tracken, Verlängerungs-Reminder |

### 🤖 KI-gestützte Analyse (Claude Sonnet)
- Extraktion: Absender, Beträge, Fristen, Fälligkeiten, Kündigungsfristen, IBAN, Referenzen
- Für Verträge: Vertragsbeginn/-ende, Kündigungsfrist in Tagen, automatische Verlängerung, Monatskosten
- Für Ausweise: Ablaufdatum → Task "verlängern" wenn < 6 Monate
- Vision-API für Scans (Bilder), Tesseract OCR für PDFs

### ⏰ Proaktive Erinnerungen
- Prioritätsbasierte Reminder-Ketten (push + email)
- **Standard:** 0 / 2 / 7 Tage vor Fälligkeit
- **Verträge:** 30 / 14 / 7 / 1 Tag vor Kündigungsfrist
- Eskalation bei überfälligen Zahlungen

### 📅 Kalender-Integration
- **Google Calendar** bidirektional (automatischer Sync alle 15 Minuten)
- Termine aus Dokumenten werden direkt in den Kalender eingetragen
- CalDAV-Support vorbereitet

### 📥 Paperless-ngx Integration
- Automatischer Import aus Paperless-ngx alle 30 Minuten
- KI analysiert OCR-Text und erstellt Tasks
- Write-back: Analyseergebnisse (Tags, Custom Fields) zurück nach Paperless

### 📱 Flutter Mobile App (Android)
- Dokumenten-Liste & Detailansicht mit Vorschau
- Task-Management
- Kalender-Ansicht
- Integrations-Verwaltung (Google Calendar)
- Push-Benachrichtigungen via Firebase FCM

## 🛠️ Tech Stack

### Backend
| Komponente | Technologie |
|------------|-------------|
| API | Python 3.13, FastAPI |
| Datenbank | PostgreSQL (SQLAlchemy ORM) |
| Task Queue | Celery + Redis |
| KI | Anthropic Claude Sonnet (Vision + Text) |
| OCR | Tesseract (PDF), Claude Vision (Bilder) |
| Auth | JWT (argon2id Passwort-Hashing) |
| Push | Firebase Cloud Messaging |

### Frontend / Mobile
| Komponente | Technologie |
|------------|-------------|
| Mobile App | Flutter (Android) |
| Web | Flutter Web |
| State | Provider |
| HTTP | Dio mit JWT-Interceptor |
| Secure Storage | flutter_secure_storage |

### Infrastruktur
| Komponente | Details |
|------------|---------|
| Server | Hetzner cax11 (ARM64, 2 vCPU, 4 GB RAM) |
| Reverse Proxy | Caddy (automatisches TLS) |
| Container | Docker Compose |
| CI/CD | GitHub Actions |
| Paperless | Paperless-ngx (selbst gehostet) |

## 🚀 Quick Start (Self-Hosted)

### Voraussetzungen
- Docker + Docker Compose
- Anthropic API Key (Claude)
- Firebase-Projekt (für Push-Benachrichtigungen, optional)
- Google Cloud OAuth-Credentials (für Kalender-Sync, optional)

### 1. Repository klonen

```bash
git clone https://github.com/commanderphu/workmate_private.git
cd workmate_private
```

### 2. Umgebungsvariablen konfigurieren

```bash
cp backend/.env.example backend/.env
```

Mindestens erforderlich in `backend/.env`:

```env
SECRET_KEY=dein-geheimes-schluessel
DATABASE_URL=postgresql+psycopg2://workmate_private:workmate_private@postgres:5432/workmate_private
CLAUDE_API_KEY=sk-ant-...

# Optional: Paperless-ngx
PAPERLESS_URL=https://deine-paperless-instanz.xyz
PAPERLESS_TOKEN=dein-paperless-token

# Optional: Google Calendar
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=https://deine-domain.xyz/api/v1/calendar/oauth/google/callback
```

### 3. Starten

```bash
docker compose up -d
```

API läuft auf `http://localhost:8000`, UI auf `http://localhost:3000`.

### 4. Ersten User anlegen

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","email":"du@example.com","password":"sicheres-passwort"}'
```

### Flutter App bauen

```bash
cd frontend
flutter pub get
flutter run --dart-define=API_URL=http://localhost:8000/api/v1
```

Oder als Release-APK:

```bash
flutter build apk --release \
  --dart-define=API_URL=https://deine-api-domain.xyz/api/v1
```

## 🏗️ Architektur

```
┌─────────────────┐     ┌──────────────────────┐
│  Flutter App    │────▶│  FastAPI Backend      │
│  (Android/Web)  │◀────│  /api/v1/...          │
└─────────────────┘     └──────────┬───────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
             ┌──────────┐  ┌──────────┐  ┌──────────┐
             │PostgreSQL│  │  Redis   │  │  Celery  │
             └──────────┘  └──────────┘  └────┬─────┘
                                              │
                          ┌───────────────────┼──────────────┐
                          ▼                   ▼              ▼
                   ┌────────────┐  ┌──────────────┐  ┌──────────┐
                   │ Claude API │  │ Paperless-ngx│  │ Google   │
                   │ (Analyse)  │  │ (Dokumente)  │  │ Calendar │
                   └────────────┘  └──────────────┘  └──────────┘
```

### Celery Beat Tasks

| Task | Intervall | Beschreibung |
|------|-----------|--------------|
| `dispatch_reminders` | 60s | Fällige Erinnerungen versenden |
| `paperless_sync` | 30 Min | Neue Docs aus Paperless importieren |
| `calendar_sync` | 15 Min | Google Calendar bidirektional synchronisieren |

## 🎯 Use Cases

### Post-Management
**Problem:** Brief kommt rein → wird zur Seite gelegt → verschwindet im Stapel → Mahnung  
**Lösung:** Scan → KI-Analyse → Auto-Reminder → Kalender-Eintrag → Eskalation bei kritischen Fristen

### Verträge & Kündigungsfristen
**Problem:** Kündigungsfrist verpasst, Vertrag verlängert sich automatisch  
**Lösung:** Vertrag scannen → KI erkennt Kündigungsfrist → Reminder 30 / 14 / 7 / 1 Tag vorher

### Ausweis / Pass
**Problem:** Ausweis läuft unbemerkt ab  
**Lösung:** Ausweis scannen → Ablaufdatum erkannt → Task "Personalausweis verlängern" + Bürgeramt-Hinweis

### Papierloses Büro
**Problem:** Alle Dokumente als Scan vorhanden, aber keine Struktur  
**Lösung:** Paperless-ngx als Archiv → Workmate importiert automatisch → KI-Analyse → Tasks

## 🤝 Contributing

Workmate Private ist Open Source! Beiträge, Ideen und Feedback sind herzlich willkommen.

Egal ob du Code beitragen, Features vorschlagen oder einfach deine ADHD-Erfahrungen teilen möchtest – jeder Input hilft.

## 📖 Die Story

Im Sommer 2020 wurde ich mit ADHD diagnostiziert. In den Jahren 2021/22 setzte ich mich intensiv mit dem Thema Neurodivergenz auseinander und kam zu einer wichtigen Erkenntnis:

**Die Welt wurde so designed, dass sie uns Neurodiverse systematisch aussortiert.**

Statt mich weiter anzupassen, stellte ich mir die Frage: **Warum bauen wir nicht Systeme, die uns inkludieren und uns in der aktuellen Welt enablen?**

Workmate Private ist meine Antwort darauf. Ein Tool, das aus persönlicher Erfahrung entstanden ist und das Problem an der Wurzel anpackt: Nicht wir müssen uns ändern, sondern die Systeme.

## 📄 Lizenz

MIT License

---

**Made with ❤️ by [CommanderPhu](https://github.com/commanderphu)**  
*Part of the Workmate ecosystem*
