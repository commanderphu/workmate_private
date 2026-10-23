# 23.10.2026 — Freitag (bis 24.10. ca. 01:00)

## Fokus
> Was ist heute das Eine, das wirklich zählt?

Prod wieder verlässlich machen: Login/Refresh, Dokumentanalyse, Kalender-Sync, Erreichbarkeit.

## Tasks
- [x] Refresh-Endpoint: fehlender `decode_token`-Import (500 seit 23.07.) — `6efb998`
- [x] Login: Benutzername oder E-Mail, Groß-/Kleinschreibung egal — `878f049`
- [x] Paperless-Import: Analyse erst nach Commit anstoßen (Dokumente blieben still `pending`) — `a58db8b`
- [x] `calendar_sync`: `Integration.is_active` → `enabled` (lief seit 22.07. nie) — `a58db8b`
- [x] Analyse: Fehlergrund in `doc_metadata.ai_error`, Parameter `notify` für Nachläufe ohne Push — `a58db8b`
- [x] Überfällige Reminder am nächsten Morgen 08:00 statt nach 2 h — `85d8dc1`
- [x] LLM-Anbieter umschaltbar (Claude oder OpenAI-kompatibel) — `59a701c`
- [x] Google-OAuth-Variablen an den Worker — `4a3a836`
- [x] Deploy: nur ein Lauf gleichzeitig (`concurrency`), nginx-Neustart nach `up -d` — `bec2b40`
- [x] Migration `0002`: doppeltes `drop_constraint` (frische Installationen blieben hängen) — `ae63123`
- [x] Tests: von 0 auf 76 (Auth, Tasks, Reminder-Schedule, Paperless-Pipeline, LLM-Anbieter); CI schluckt Testfehler nicht mehr
- [x] Dev-Tooling: venv (Python 3.13 via uv), pre-commit (flake8 mit CI-Regeln), Auto-Reload, Makefile, Sync-Flags für die Dev-Instanz
- [x] Prod: Let's-Encrypt-Zertifikat erneuert (war seit 19.09. abgelaufen → Cloudflare 526), Renewal-Hooks gesetzt
- [x] Prod: aktuelle `docker-compose.prod.yml` auf den Server gebracht (lag seit 21.07. unverändert)

## Notizen & Gedanken

**Warum seit Ende August keine Dokumentanalyse mehr lief:** Das Claude-API-Guthaben ist aufgebraucht. Zusätzlich stieß der Import die Analyse vor dem Commit an, sodass betroffene Dokumente nicht als `failed`, sondern still als `pending` liegen blieben. Beides ist jetzt sichtbar bzw. behoben; die Analyse selbst wartet auf einen anderen Anbieter (#5).

**Warum Compose-Änderungen nie auf Prod ankamen:** Das `git pull` im Deploy-Skript scheitert still, weil `/opt/workmate-private` kein Git-Checkout ist (#3). Images wurden aktualisiert, die Konfiguration nicht.

**Warum Prod zwischendurch 502/526 lieferte:**
- 502: nginx hält nach neu erstelltem Backend-Container die alte IP — jetzt Neustart im Deploy-Workflow, saubere Lösung in #8.
- 526: Zertifikat abgelaufen; certbot `standalone` konnte Port 80 nie binden, weil der nginx-Container ihn hält. Renewal-Hooks stoppen/starten nginx jetzt.

**Kalender:** Der Sync läuft jetzt technisch, Google lehnt die Refresh-Tokens aber ab (`invalid_grant`) — vermutlich OAuth-App im Testmodus (#4).

**Lehren:**
- Ein grüner Job heißt nicht, dass jeder Schritt lief — Deploy-Skripte brauchen `set -e`.
- Tests müssen ohne lokale `.env` laufen; CI-Bedingungen lokal nachstellen (`CLAUDE_API_KEY= make test`).

## Offene Punkte
Getrackt als GitHub Issues:
- #3 Deploy überträgt `docker-compose.prod.yml` nicht
- #4 Google Calendar: `invalid_grant`
- #5 KI-Analyse auf anderen Anbieter umstellen, fehlgeschlagene Dokumente nachholen
- #6 Dokumente ohne OCR-Text werden still als `done` markiert
- #7 Login-Feld beschriften („Benutzername oder E-Mail“)
- #8 nginx: Backend dynamisch auflösen
- #9 GitHub Actions auf Node 24
- #1, #2 (Paperless bidirektional, Push bei E-Mail-Import) unverändert

## Log
- Projektstand aufgenommen, Doku in Vault, `CLAUDE.md` und `SESSION_NOTES.md`
- Refresh-Bug gefixt und deployt, mit echtem Token auf Prod verifiziert
- Dev-Setup aufgeräumt: Sync-Flags, `celerybeat-schedule` aus Git, Dev-DB auf Migrations-Head
- Tests und pre-commit eingeführt, CI-Lücke (`|| true`) geschlossen
- Prod-Ausfall (nginx/502) — Ursache gefunden, Deploy-Workflow angepasst
- Login auf dem Handy getestet, Login-Fix für Groß-/Kleinschreibung
- Dokumentanalyse untersucht: Commit-Bug + leeres API-Guthaben; Nachlauf ohne Push
- Anbieter-Umschaltung gebaut (Weg ohne Kosten)
- Nachts: Prod 526 (Zertifikat), Compose-Stand auf dem Server, Kalender-Sync bis `invalid_grant`
