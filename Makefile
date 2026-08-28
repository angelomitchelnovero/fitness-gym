.PHONY: help up down logs ps backend backend-install frontend frontend-install test lint format

help:
	@echo "FitnessGym dev commands"
	@echo "  make up               Start PostgreSQL + Mailpit via Docker Compose"
	@echo "  make down             Stop Docker Compose services"
	@echo "  make backend-install  Install backend deps (editable + dev extras)"
	@echo "  make backend          Run FastAPI dev server"
	@echo "  make frontend-install Install frontend deps"
	@echo "  make frontend         Run Vite dev server"
	@echo "  make test             Run backend tests"
	@echo "  make lint             Run backend lint checks"
	@echo "  make format           Auto-format backend code"

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

ps:
	docker compose ps

backend-install:
	cd backend && python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"

backend:
	cd backend && . .venv/bin/activate && uvicorn app.main:app --reload --port 8000

frontend-install:
	cd frontend && npm install

frontend:
	cd frontend && npm run dev

test:
	cd backend && . .venv/bin/activate && pytest

lint:
	cd backend && . .venv/bin/activate && ruff check app tests && mypy app

format:
	cd backend && . .venv/bin/activate && ruff check --fix app tests && ruff format app tests
