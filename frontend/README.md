# Workmate Private Frontend

Flutter-basierte App für Workmate Private (Web, Android, iOS).

## Setup

### Voraussetzungen

- Flutter SDK 3.16.0+
- Dart 3.2.0+

### Installation

1. Dependencies installieren:
```bash
flutter pub get
```

2. Environment-Variablen setzen:
```bash
cp .env.example .env
# .env bearbeiten falls nötig
```

### Entwicklung

#### Web
```bash
flutter run -d chrome
```

#### Android
```bash
flutter run -d android
```

#### iOS (nur macOS)
```bash
flutter run -d ios
```

## Build

### Web
```bash
flutter build web
```

### Android APK
```bash
flutter build apk
```

### iOS
```bash
flutter build ios
```

## Tests

```bash
flutter test
```

## Code Analyse

```bash
flutter analyze
```

## Code Formatierung

```bash
flutter format lib/
```
