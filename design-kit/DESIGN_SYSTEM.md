# Workmate Private – Open Source Design System

> **Open Source. Privacy First. Neurodivergent by Design.**

Dieses Dokument definiert die visuelle Grundlage von **Workmate Private**.  
Das Design soll ruhig, freundlich, verlässlich und möglichst reizarm wirken. Es unterstützt die Kernidee des Projekts: Organisation soll entlasten statt zusätzlichen Druck erzeugen.

---

## 1. Markenidee

**Workmate Private** ist ein persönlicher Open-Source-Assistent für:

- Dokumente
- Fristen und Erinnerungen
- Termine und Kalender-Synchronisation
- Verträge und wiederkehrende Verpflichtungen
- selbstbestimmte, datenschutzfreundliche Organisation

### Markenwerte

| Wert | Bedeutung |
|---|---|
| Unterstützend | Die Anwendung begleitet, ohne zu bevormunden. |
| Klar | Informationen werden verständlich und priorisiert dargestellt. |
| Vertrauenswürdig | Datenschutz und Transparenz stehen im Vordergrund. |
| Entlastend | Weniger mentale Last, weniger vergessene Aufgaben. |
| Inklusiv | Neurodivergente Menschen werden von Anfang an mitgedacht. |
| Offen | Code, Entscheidungen und Entwicklung bleiben nachvollziehbar. |

### Positionierung

> **Organisation, die mit dir arbeitet.**

Alternativer Claim:

> **Papierkram im Griff. Kopf frei.**

---

## 2. Logo und App-Icon

Das zentrale Symbol verbindet drei Bedeutungen:

1. **W** – Workmate
2. **Haken** – erledigt, sicher, unter Kontrolle
3. **Dokument-/Sprechblasenform** – Papierkram und persönlicher Begleiter

Die Form ist bewusst weich und abgerundet. Sie soll nicht wie eine sterile Behörden- oder Business-App wirken.

### Schutzraum

Rund um das Logo muss mindestens die Höhe des kleinen Buchstabens **w** als freier Raum bestehen.

### Mindestgrößen

| Verwendung | Mindestgröße |
|---|---:|
| Favicon | 16 × 16 px |
| UI-Icon | 24 × 24 px |
| App-Icon | 72 × 72 px |
| Horizontales Logo | 160 px Breite |
| Print | 25 mm Breite |

### Nicht erlaubt

- Logo verzerren
- Farben frei austauschen
- starke Schatten oder Glows ergänzen
- Symbol und Wortmarke überlappen
- Logo auf unruhigen Fotos ohne Kontrastfläche verwenden
- das Symbol mit proprietären Marken kombinieren

---

## 3. Farbpalette

### Hauptfarben

| Token | Hex | Verwendung |
|---|---|---|
| `brand-primary` | `#F59E0B` | Primäre Aktionen, aktive Navigation |
| `brand-primary-light` | `#FDBA1F` | Highlights, Hover, Illustration |
| `brand-success` | `#10B981` | Erledigt, sicher, positive Rückmeldung |
| `background-dark` | `#1E1E1E` | Haupt-Hintergrund im Dark Mode |
| `surface-dark` | `#2D2D2D` | Cards, Dialoge, Navigation |
| `border-dark` | `#3A3A3A` | Linien und dezente Abgrenzungen |
| `text-primary-dark` | `#F5F7FA` | Haupttext im Dark Mode |
| `white` | `#FFFFFF` | Logo und maximale Hervorhebung |

### Semantische Farben

| Status | Empfehlung |
|---|---|
| Erfolg | `#10B981` |
| Information | `#3B82F6` |
| Warnung | `#FBBF24` |
| Fehler / überfällig | `#EF4444` |
| Neutral | `#6B7280` |

Farben dürfen niemals die einzige Informationsquelle sein. Status müssen zusätzlich mit Text oder Icons gekennzeichnet werden.

---

## 4. Typografie

### Primäre Schrift

**Inter**

Fallback:

```css
font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
```

Inter ist frei verfügbar, gut lesbar und eignet sich für Web, Android und Desktop.

### Typografische Skala

| Stil | Größe | Zeilenhöhe | Gewicht |
|---|---:|---:|---:|
| Display | 48 px | 56 px | 700 |
| H1 | 36 px | 44 px | 700 |
| H2 | 28 px | 36 px | 650 |
| H3 | 22 px | 30 px | 600 |
| Body Large | 18 px | 28 px | 400 |
| Body | 16 px | 24 px | 400 |
| Body Small | 14 px | 20 px | 400 |
| Label | 13 px | 18 px | 600 |
| Caption | 12 px | 16 px | 400 |

Längere Texte sollten nicht komplett in Großbuchstaben geschrieben werden.

---

## 5. Abstände und Raster

Workmate nutzt ein **8-Punkt-Raster**.

| Token | Wert |
|---|---:|
| `space-1` | 4 px |
| `space-2` | 8 px |
| `space-3` | 12 px |
| `space-4` | 16 px |
| `space-5` | 24 px |
| `space-6` | 32 px |
| `space-7` | 48 px |
| `space-8` | 64 px |

### Radien

| Element | Radius |
|---|---:|
| Kleine Controls | 8 px |
| Inputs und Buttons | 12 px |
| Cards | 16 px |
| Große Panels | 24 px |
| Pill / Badge | 999 px |

---

## 6. Komponenten

### Primärer Button

- Hintergrund: `#F59E0B`
- Text: `#111827`
- Mindesthöhe: 44 px
- Radius: 12 px
- Kein vollständig deaktivierter Button ohne Erklärung

### Sekundärer Button

- Transparenter Hintergrund
- 1 px Border `#3A3A3A`
- Heller Text
- Hover mit leicht erhöhter Oberfläche

### Inputs

- Label immer sichtbar
- Placeholder niemals als alleinige Beschriftung
- Fehler direkt unter dem Feld erklären
- Fokus-Ring mindestens 2 px

### Cards

- Informationen nach Dringlichkeit sortieren
- maximal eine primäre Aktion
- kritische Fristen klar, aber nicht alarmistisch darstellen
- ausklappbare Details bevorzugen

### Status-Badges

Empfohlene Begriffe:

- **Erledigt**
- **Bald fällig**
- **Überfällig**
- **In Bearbeitung**
- **Keine Aktion nötig**
- **Prüfung empfohlen**

---

## 7. Icon-Stil

Empfohlen wird **Lucide Icons**.

- 2 px Strichstärke
- abgerundete Enden
- keine Mischung verschiedener Icon-Stile
- Standardgröße: 20 oder 24 px
- Icons immer mit verständlichem Label, sofern die Bedeutung nicht allgemein bekannt ist

### Kern-Icons

| Bereich | Icon |
|---|---|
| Dashboard | `house` |
| Dokumente | `file-text` |
| Termine | `calendar-days` |
| Erinnerungen | `bell` |
| Aufgaben | `circle-check-big` |
| Verträge | `file-signature` |
| Sicherheit | `shield-check` |
| Einstellungen | `settings` |
| Open Source | `code-xml` |
| Datenschutz | `lock-keyhole` |

---

## 8. Dark und Light Mode

### Dark Mode

- Standard-Hintergrund: `#1E1E1E`
- Oberfläche: `#2D2D2D`
- Text: `#F5F7FA`
- Orange nur für wichtige Interaktionen verwenden

### Light Mode

- Hintergrund: `#F7F8FA`
- Oberfläche: `#FFFFFF`
- Text: `#1E1E1E`
- Border: `#D7DBE0`

Beide Modi müssen vollständig nutzbar sein. Dark Mode darf nicht die einzige unterstützte Darstellung bleiben.

---

## 9. Barrierefreiheit und Neurodivergent-first UX

### Verbindliche Prinzipien

- WCAG-AA-Kontraste einhalten
- keine automatisch startenden Animationen
- Animationen unter `prefers-reduced-motion` deaktivieren
- keine blinkenden Elemente
- klare Seitentitel und Breadcrumbs
- Aufgaben in kleine, verständliche Schritte zerlegen
- sichere Rückgängig-Funktion anbieten
- keine manipulativen Dark Patterns
- Erinnerungen dürfen pausiert oder angepasst werden
- kritische Aktionen müssen erklärbar sein

### Sprache

Gut:

> Die Rechnung ist seit zwei Tagen fällig. Möchtest du sie als erledigt markieren oder später erinnert werden?

Nicht gut:

> Du hast die Rechnung schon wieder vergessen!

Die Anwendung unterstützt. Sie bewertet nicht.

---

## 10. Open-Source-Grundsätze

- Alle offiziellen Design-Assets werden gemeinsam mit dem Code versioniert.
- Bevorzugte Asset-Formate sind SVG und offene Textformate.
- Externe Schriftarten müssen frei lizenzierbar sein.
- Designentscheidungen dürfen öffentlich diskutiert werden.
- Community-Beiträge sollen den definierten Markenwerten und Accessibility-Regeln folgen.
- Die Marke darf nicht zur Irreführung oder zur Darstellung einer offiziellen Partnerschaft verwendet werden.

### Empfohlene Asset-Lizenz

Für Logos und Markenassets empfiehlt sich eine gesonderte Regelung im Repository:

> Der Quellcode steht unter der Projektlizenz. Name, Logo und Markenassets dürfen für Beiträge, Forks und Berichterstattung genutzt werden, jedoch nicht zur Vortäuschung einer offiziellen Version oder Partnerschaft.

Dies ist keine Rechtsberatung. Vor einer kommerziellen oder markenrechtlichen Nutzung sollte die Regelung geprüft werden.

---

## 11. Design Tokens

```css
:root {
  --wm-primary: #F59E0B;
  --wm-primary-light: #FDBA1F;
  --wm-success: #10B981;

  --wm-background: #1E1E1E;
  --wm-surface: #2D2D2D;
  --wm-border: #3A3A3A;

  --wm-text-primary: #F5F7FA;
  --wm-text-secondary: #A7ADB7;

  --wm-radius-control: 12px;
  --wm-radius-card: 16px;
  --wm-radius-panel: 24px;

  --wm-space-1: 4px;
  --wm-space-2: 8px;
  --wm-space-3: 12px;
  --wm-space-4: 16px;
  --wm-space-5: 24px;
  --wm-space-6: 32px;
}
```

---

## 12. Dateistruktur

```text
assets/
├── branding/
│   ├── workmate-logo-horizontal-dark.svg
│   └── workmate-logo-horizontal-light.svg
└── icons/
    ├── workmate-app-icon.svg
    ├── workmate-monochrome.svg
    ├── favicon.svg
    ├── favicon.ico
    ├── favicon-16x16.png
    ├── favicon-32x32.png
    ├── apple-touch-icon.png
    ├── workmate-icon-192x192.png
    ├── workmate-icon-512x512.png
    ├── workmate-icon-1024x1024.png
    ├── site.webmanifest
    └── android/
        ├── workmate-background.svg
        ├── workmate-foreground.svg
        ├── workmate-background-432.png
        └── workmate-foreground-432.png
```

---

## 13. Verwendung im Vue-/Web-Frontend

Dateien nach `public/` kopieren:

```text
public/
├── favicon.svg
├── favicon.ico
├── favicon-16x16.png
├── favicon-32x32.png
├── apple-touch-icon.png
├── site.webmanifest
└── icons/
    ├── workmate-icon-192x192.png
    └── workmate-icon-512x512.png
```

Danach den Inhalt aus `HTML_HEAD_SNIPPET.html` in die HTML-Hauptdatei übernehmen.

---

## 14. Figma-Import

Figma kann die enthaltenen SVG-Dateien direkt importieren:

1. Neue Figma-Seite `Workmate Brand` erstellen.
2. SVG-Dateien hineinziehen.
3. Farben als lokale Variables anlegen.
4. Inter als lokale Text Styles definieren.
5. Logo- und Icon-Frames als Components speichern.
6. Für App-Icons keine nachträglichen Effekte hinzufügen.

---

## 15. Versionsverwaltung

Empfohlene Commit-Nachricht:

```text
feat(branding): add Workmate design system and icon pack
```

Designset-Version: **1.0.0**
