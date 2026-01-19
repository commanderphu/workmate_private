# Workmate Private Backend

FastAPI-basiertes Backend für Workmate Private.

## Setup

### Lokale Entwicklung

1. Python Virtual Environment erstellen:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# oder
.venv\Scripts\activate  # Windows
```

2. Dependencies installieren:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

3. Environment-Variablen setzen:
```bash
cp .env.example .env
# .env bearbeiten und API-Keys eintragen
```

4. Server starten:
```bash
uvicorn app.main:app --reload
```

Server läuft dann auf: http://localhost:8000

### Docker

```bash
cd ..
docker-compose up
```

## API-Dokumentation

Nach dem Start erreichbar unter:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Tests

```bash
pytest
```

Mit Coverage:
```bash
pytest --cov=app --cov-report=html
```

## Code Quality

```bash
# Linting
flake8 app

# Type Checking
mypy app

# Formatting
black app
```
