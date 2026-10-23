# Workmate Private — Dev-Setup (Root-docker-compose.yml auf cisco)
# Übersicht: make help
#
# Für Prod nicht gedacht: Prod läuft über docker-compose.prod.yml + GitHub Actions.

SHELL := /bin/bash
.DEFAULT_GOAL := help

COMPOSE   := docker compose
BACKEND   := workmate_private_backend
WORKER    := workmate_private_celery
BEAT      := workmate_private_celery_beat
SERVICES  := $(BACKEND) $(WORKER) $(BEAT)

VENV      := venv
UV        := $(HOME)/.local/share/uv-bootstrap/bin/uv
API_URL   := https://api.workmate-private.intern.phudevelopement.xyz
BACKUP_DIR := $(HOME)

.PHONY: help up down recreate restart restart-workers ps logs logs-worker logs-beat \
        shell health backup migrate db-current venv lint test pre-commit

help: ## Diese Übersicht
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# ── Container ────────────────────────────────────────────────

up: ## Dev-Stack starten
	$(COMPOSE) up -d

down: ## Dev-Stack stoppen
	$(COMPOSE) down

recreate: ## Backend, Worker, Beat neu erstellen (nötig nach .env-Änderung)
	$(COMPOSE) up -d --no-build --force-recreate $(SERVICES)

restart: ## Backend, Worker, Beat neu starten
	docker restart $(SERVICES)

restart-workers: ## Nur Worker + Beat neu starten (laden Code nicht selbst neu)
	docker restart $(WORKER) $(BEAT)

ps: ## Status der Dev-Container
	@docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -E 'NAMES|workmate_private'

logs: ## Backend-Logs folgen
	docker logs -f --tail 100 $(BACKEND)

logs-worker: ## Celery-Worker-Logs folgen
	docker logs -f --tail 100 $(WORKER)

logs-beat: ## Celery-Beat-Logs folgen
	docker logs -f --tail 100 $(BEAT)

shell: ## Shell im Backend-Container
	docker exec -it $(BACKEND) bash

health: ## Health-Check des Dev-Backends
	@curl -fsS -m 5 $(API_URL)/health && echo

# ── Datenbank ────────────────────────────────────────────────

backup: ## Dev-DB sichern (pg_dump nach ~/workmate_private-dev-db-sicherung-*.sql.gz)
	@set -o pipefail; \
	url=$$(grep '^DATABASE_URL=' .env | cut -d= -f2- | sed 's/+psycopg2//; s/@central_postgres:/@localhost:/'); \
	out=$(BACKUP_DIR)/workmate_private-dev-db-sicherung-$$(date +%Y%m%d-%H%M%S).sql.gz; \
	docker exec central_postgres pg_dump --no-owner "$$url" | gzip > "$$out" && \
	zcat "$$out" | grep -q 'dump complete' && echo "Backup: $$out"

migrate: backup ## Backup ziehen, dann alembic upgrade head
	docker exec $(BACKEND) alembic upgrade head

db-current: ## Aktuelle Alembic-Revision der Dev-DB
	@docker exec $(BACKEND) alembic current 2>&1 | tail -1

# ── Lokales Tooling ──────────────────────────────────────────

venv: ## venv (Python 3.13) anlegen bzw. Pakete aktualisieren
	@test -x $(UV) || { python3 -m venv $(HOME)/.local/share/uv-bootstrap && $(HOME)/.local/share/uv-bootstrap/bin/pip install -q uv; }
	@test -d $(VENV) || $(UV) venv $(VENV) --python 3.13
	VIRTUAL_ENV=$(CURDIR)/$(VENV) $(UV) pip install -r backend/requirements.txt -r backend/requirements-dev.txt
	$(VENV)/bin/pre-commit install

lint: ## flake8 mit den harten Regeln der Backend-CI
	cd backend && ../$(VENV)/bin/flake8 app --count --select=E9,F63,F7,F82 --show-source --statistics

test: ## pytest im Backend
	cd backend && ../$(VENV)/bin/pytest

pre-commit: ## Alle pre-commit-Hooks über alle Dateien
	$(VENV)/bin/pre-commit run --all-files
