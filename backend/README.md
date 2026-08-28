# FitnessGym Backend

FastAPI + SQLAlchemy + Alembic.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

## Test

```bash
pytest
```

## Lint

```bash
ruff check app tests
mypy app
```
