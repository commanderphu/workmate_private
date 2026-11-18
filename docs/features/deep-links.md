# Deep Links (Android)

Seit 18.11.2026 (`460b9a4`) lässt sich die Android-App aus dem Browser starten, z. B. über den Knopf „Workmate-App öffnen“ im phu-dashboard.

## Unterstützt

| Link | Wirkung |
|---|---|
| `workmate://open` | Öffnet die App auf der Startseite (bzw. holt die laufende Instanz nach vorn) |
| `intent://open#Intent;scheme=workmate;package=xyz.phudevelopement.workmate_private;S.browser_fallback_url=…;end` | Dasselbe für Chromium-Browser (Brave, Chrome). Ist die App nicht installiert, öffnet der Browser die Fallback-URL |

Umgesetzt in `frontend/android/app/src/main/AndroidManifest.xml`:

- Zusätzlicher Intent-Filter an der `.MainActivity` mit `VIEW`, `DEFAULT`, `BROWSABLE`, `scheme=workmate`, `host=open`. Browser dürfen nur Activities mit Kategorie `BROWSABLE` starten. Ein Intent-Link nur mit Paketnamen (MAIN/LAUNCHER) funktioniert deshalb nicht.
- `flutter_deeplinking_enabled=false`: Flutter gibt den Link-Pfad nicht an den Navigator weiter.

## Einschränkung

**Pfade werden derzeit ignoriert.** `workmate://open/tasks` oder `workmate://open/documents/123` öffnen ebenfalls nur die Startseite. Die App hat keine benannten Routen. Gezielte Ziele bräuchten einen Router und das Auswerten des Links, z. B. mit `app_links`.

## Möglicher Ausbau

- Pfade wie `workmate://open/tasks` auf einzelne Seiten routen
- Android App Links für `https://workmate-private.phudevelopement.xyz` über `/.well-known/assetlinks.json`, damit auch normale https-Links die App öffnen

## Testen

```bash
adb shell am start -W -a android.intent.action.VIEW -c android.intent.category.BROWSABLE -d "workmate://open"
```

Erwartet: `Status: ok`, `Activity: xyz.phudevelopement.workmate_private/.MainActivity`.
