# Architektur-Entscheidungsprotokoll (ADR)

## Übersicht

Dieses Dokument verfolgt wichtige technische und architektonische Entscheidungen, die während der Entwicklung von Workmate Private getroffen wurden.

**Format:** Leichtgewichtige ADR (nicht strikt)
**Zweck:** Dokumentieren *warum* Entscheidungen getroffen wurden, nicht nur *was*

---

## ADR-001: Projekt-Sprache Deutsch

**Datum:** 19.01.2026
**Status:** Akzeptiert
**Entscheider:** Joshua

### Kontext
Workmate Private wird von einem deutschen Entwickler (Joshua) für die ADHD-Community entwickelt, mit initialem Fokus auf deutschsprachige Nutzer.

### Entscheidung
- **Benutzerseitige Dokumentation:** Deutsch (README, Konzept, Features)
- **Code, Kommentare, Commit-Nachrichten:** Englisch (Industriestandard)
- **Entwicklungs-Dokumentation:** Englisch (für potenzielle internationale Mitwirkende)

### Begründung
- Primäre Nutzer sind deutsche ADHD-Community
- Code in Englisch ist Standardpraxis
- Hält die Codebasis für internationale Entwickler zugänglich
- Dokumentation kann später bei Bedarf übersetzt werden

### Konsequenzen
- Deutschsprachige Nutzer fühlen sich stärker einbezogen
- Technische Schuld: Möglicherweise spätere Übersetzung für Wachstum erforderlich
- Gemischte Sprache im Repository (akzeptabler Kompromiss)

---

## ADR-002: Flutter für Frontend

**Datum:** 19.01.2026
**Status:** Akzeptiert
**Entscheider:** Joshua

### Kontext
Benötigt plattformübergreifendes Frontend (Web + Mobile). Optionen: React Native, Flutter, Separate Apps.

### Entscheidung
Verwende **Flutter** für alle Plattformen (Web, Android, iOS).

### Begründung
**Vorteile:**
- Einzelne Codebasis für Web + Mobile
- Native Performance
- Material Design out-of-the-box (ADHD-freundliche saubere UI)
- Wachsendes Ökosystem
- Joshua möchte Dart/Flutter lernen

**Nachteile:**
- Neue Sprache (Dart) zu lernen
- Web-Support noch in Entwicklung
- Größere Bundle-Größe als reines Web

### Betrachtete Alternativen
- **React Native:** Reifer, aber schlechtere Web-Unterstützung
- **Vue.js + Native Apps:** Doppelte Arbeit, schwerer zu warten
- **Nur PWA:** Keine nativen Mobile-Features (Kamera, Benachrichtigungen)

### Konsequenzen
- Schnellere Entwicklung nach initialer Lernkurve
- Konsistente UX über Plattformen hinweg
- Dart lernen notwendig (akzeptabel, Joshua will dies)

---

## ADR-003: Python + FastAPI für Backend

**Datum:** 19.01.2026
**Status:** Akzeptiert
**Entscheider:** Joshua

### Kontext
Backend-Framework-Wahl. Optionen: Django, FastAPI, Node.js, Go.

### Entscheidung
Verwende **Python 3.11+ mit FastAPI**.

### Begründung
**Vorteile:**
- Joshua kennt bereits Python (von WorkmateOS)
- FastAPI ist modern, asynchron, schnell
- Exzellentes AI/ML-Bibliotheks-Ökosystem (anthropic, tesseract)
- Type Hints + automatische API-Dokumentation
- Einfach zu deployen

**Nachteile:**
- Etwas langsamer als Go/Rust (akzeptabel für unsere Größenordnung)

### Betrachtete Alternativen
- **Django:** Zu schwer, wir brauchen Django ORM/Admin nicht
- **Node.js:** Müsste gelernt werden, Python besser für AI-Integration
- **Go:** Schneller, aber steilere Lernkurve

### Konsequenzen
- Schnelle Entwicklung (vertrauter Stack)
- Großartige AI-Integration
- Möglicherweise Optimierung bei Skalierung erforderlich (zukünftiges Problem)

---

## ADR-004: SQLite + PostgreSQL Hybrid

**Datum:** 19.01.2026
**Status:** Akzeptiert
**Entscheider:** Joshua

### Kontext
Datenbankwahl für Self-Hosted vs. Cloud-Deployment.

### Entscheidung
Unterstütze **sowohl SQLite als auch PostgreSQL** über SQLAlchemy-Abstraktion.

### Begründung
- **SQLite:** Perfekt für Self-Hosted, keine Konfiguration, einzelner Benutzer
- **PostgreSQL:** Produktionsreif für Cloud, Multi-User, Skalierung
- SQLAlchemy macht es einfach, beide zu unterstützen

### Konsequenzen
- Flexibler für Benutzer
- Etwas komplexer (beide müssen getestet werden)
- Migrationspfad: SQLite → PostgreSQL einfach

---

## ADR-005: Claude API + Ollama Dual-Unterstützung

**Datum:** 19.01.2026
**Status:** Akzeptiert
**Entscheider:** Joshua

### Kontext
KI für Dokumentenanalyse. Cloud vs. Lokal.

### Entscheidung
Unterstütze **sowohl Claude API (Cloud) als auch Ollama (lokal)** mit Strategy Pattern.

### Begründung
**Claude API:**
- Beste Genauigkeit für Dokumentenanalyse
- Vision API für Bilder
- Zuverlässig, schnell
- Kostet Geld

**Ollama:**
- Privatsphäre (lokal)
- Kostenlos
- Funktioniert offline
- Benötigt GPU für gute Performance

**Warum beide?**
- Benutzer können basierend auf Bedürfnissen wählen
- Kostenbewusste Benutzer nutzen Ollama
- Privatsphäre-fokussierte Benutzer nutzen Ollama
- Cloud-Benutzer nutzen Claude für beste Ergebnisse

### Konsequenzen
- Mehr Code-Komplexität (Strategy Pattern)
- Beide müssen getestet werden
- Bessere Benutzer-Wahlmöglichkeiten

---

## ADR-006: Open Source (MIT-Lizenz)

**Datum:** 19.01.2026
**Status:** Akzeptiert
**Entscheider:** Joshua

### Kontext
Lizenzmodell für Workmate Private.

### Entscheidung
**Open Source mit MIT-Lizenz** (finale Lizenz TBD, tendiert zu MIT).

### Begründung
**Warum Open Source:**
- Vertrauen & Transparenz für ADHD-Community
- Community-Beiträge
- Rückgabe an Neuro-Community
- Portfolio-Stück für K.I.T. Solutions

**Warum MIT (vs. GPL):**
- Permissiver
- Einfacher für andere zu integrieren
- Nicht Copyleft (Benutzer können frei forken & modifizieren)

### Monetarisierungs-Strategie
- Kern = Für immer kostenlos
- Optionaler bezahlter Hosting-Service
- Optionale Support-/Setup-Services
- Niemals Kern-ADHD-Features hinter Paywall

### Konsequenzen
- Kann Konkurrenten nicht daran hindern, Code zu nutzen (akzeptabel)
- Community-gesteuerte Entwicklung
- Goodwill in ADHD-Community

---

## ADR-007: Erinnerungs-Eskalations-Strategie

**Datum:** 19.01.2026
**Status:** Akzeptiert
**Entscheider:** Joshua

### Kontext
Wie stellt man sicher, dass ADHD-Benutzer Erinnerungen nicht ignorieren?

### Entscheidung
**Mehrstufige Eskalation mit zunehmender Frequenz und Kanälen.**

**Stufen:**
1. Info (7 Tage vorher): 1x Push
2. Warnung (2 Tage vorher): Täglich, Push + E-Mail
3. Dringend (<2 Tage): 4x täglich, Push + E-Mail + SMS
4. Kritisch (überfällig): Stündlich, alle Kanäle + Smart Home

### Begründung
**ADHD-spezifisch:**
- Einzelne Erinnerung = leicht zu ignorieren
- Eskalation entspricht Dringlichkeitswahrnehmung
- Multi-Kanal = schwerer zu übersehen
- Physische Alarme (Smart Home) funktionieren besser bei ADHD

### Konsequenzen
- Komplexere Erinnerungs-Logik
- Risiko, Benutzer zu nerven (abgemildert durch Ruhezeiten)
- Höhere Benachrichtigungskosten (SMS, API-Aufrufe)
- **Aber:** Verhindert tatsächlich vergessene Fristen

---

## ADR-008: Docker Compose für Deployment

**Datum:** 19.01.2026
**Status:** Akzeptiert
**Entscheider:** Joshua

### Kontext
Deployment-Strategie für Self-Hosting-Benutzer.

### Entscheidung
Primäre Deployment-Methode: **Docker Compose**.

### Begründung
**Vorteile:**
- Einfaches Setup (ein Befehl)
- Konsistente Umgebung
- Portabel
- Beinhaltet alle Services (postgres, redis, celery)
- Standard in Self-Hosting-Community

**Nachteile:**
- Erfordert Docker-Kenntnisse (akzeptabel, Zielgruppe ist technikaffin)

### Betrachtete Alternativen
- **Manuelle Installation:** Zu komplex, zu viele Abhängigkeiten
- **Kubernetes:** Overkill für Einzelbenutzer
- **Snap/Flatpak:** Begrenzt, weniger flexibel

### Konsequenzen
- Großartige DX für Self-Hoster
- Gute Docker-Dokumentation erforderlich
- Alternative manuelle Installations-Dokumentation für fortgeschrittene Benutzer

---

## ADR-009: Paperless-ngx als optionale Integration

**Datum:** 19.01.2026
**Status:** Akzeptiert
**Entscheider:** Joshua

### Kontext
Viele Power-User nutzen bereits Paperless-ngx. Konkurrieren oder integrieren?

### Entscheidung
**Integrieren, nicht konkurrieren.** Paperless-ngx ist optionale Integration.

### Begründung
- Paperless ist etabliert, exzellent im Archivieren
- Wir sind besser im proaktiven Task-Management
- Integration = Beste beider Welten
- Vermeidet Neuerfindung des Rades
- Zielt auf unterschiedliche Anwendungsfälle ab (Archivierung vs. Aktion)

### Konsequenzen
- Komplexer (aber optional)
- Spricht Power-User an
- Positioniert Workmate als "intelligente Schicht", nicht Ersatz

---

## ADR-010: Home Assistant für Smart Home

**Datum:** 19.01.2026
**Status:** Akzeptiert
**Entscheider:** Joshua

### Kontext
Smart-Home-Integration für physische Erinnerungen.

### Entscheidung
Primäre Integration: **Home Assistant + MQTT**.

### Begründung
- Home Assistant ist die führende Open-Source-Smart-Home-Plattform
- MQTT ist Standard für IoT
- Beide entsprechen Self-Hosting-Philosophie
- Große Community, viele Integrationen
- Privatsphäre-fokussiert

### Betrachtete Alternativen
- **Direkte Geräte-APIs:** Zu viele zu unterstützen
- **Cloud-Services (Alexa/Google):** Privatsphäre-Bedenken
- **Custom Protocol:** Neuerfindung des Rades

### Konsequenzen
- Leistungsstarke Integration für diejenigen, die sie nutzen
- Komplex für Nicht-Home-Assistant-Benutzer (akzeptabel, es ist optional)

---

## ADR-011: Keine nativen Mobile-Push-Benachrichtigungen (Noch)

**Datum:** 19.01.2026
**Status:** Akzeptiert (Temporär)
**Entscheider:** Joshua

### Kontext
Push-Benachrichtigungen auf Mobile erfordern Firebase (Android) oder APNs (iOS).

### Entscheidung
**Phase 1: Nur Flutter Local Notifications verwenden.**
**Phase 2+: Firebase für echte Push-Benachrichtigungen hinzufügen.**

### Begründung
- Lokale Benachrichtigungen funktionieren für MVP, wenn App läuft
- Firebase-Setup erhöht Komplexität
- Fokus auf Kern-Features zuerst
- Kann später ohne Breaking Changes hinzugefügt werden

### Konsequenzen
- Erinnerungen funktionieren nur wenn App offen ist (Einschränkung)
- Firebase muss in Phase 2 hinzugefügt werden
- Benutzer könnten sich beschweren (abgemildert durch E-Mail/SMS-Fallback)

---

## ADR-012: Monatliche Roadmap-Reviews

**Datum:** 19.01.2026
**Status:** Akzeptiert
**Entscheider:** Joshua

### Kontext
ADHD macht langfristige Planung schwierig. Wie bleibt man auf Kurs?

### Entscheidung
**Roadmap monatlich überprüfen, bei Bedarf anpassen.**

### Begründung
- Flexibilität für ADHD-Gehirn
- Feedback-gesteuerte Entwicklung
- Keine starren Fristen = weniger Stress
- Fortschritt vor Perfektion

### Konsequenzen
- Roadmap ist lebendes Dokument
- Termine sind Schätzungen, keine Versprechen
- Community versteht dies (ADHD-fokussiertes Projekt)

---

## Vorlage für neue ADRs
```markdown
## ADR-XXX: Titel

**Datum:** JJJJ-MM-TT
**Status:** Vorgeschlagen | Akzeptiert | Veraltet | Ersetzt
**Entscheider:** Name(n)

### Kontext
Was ist das Problem/die zu treffende Entscheidung?

### Entscheidung
Was haben wir entschieden?

### Begründung
Warum diese Entscheidung?
- Vorteile
- Nachteile
- ADHD-spezifische Überlegungen (falls relevant)

### Betrachtete Alternativen
Was haben wir sonst noch überlegt?

### Konsequenzen
Was sind die Ergebnisse (positiv und negativ)?
```

---

## Entscheidungs-Status

- **Vorgeschlagen:** In Diskussion
- **Akzeptiert:** Entschieden und implementiert
- **Veraltet:** Nicht mehr relevant
- **Ersetzt:** Durch neuere Entscheidung ersetzt

---

**Lebendes Dokument:** Entscheidungen werden hinzugefügt, während sich das Projekt entwickelt.
