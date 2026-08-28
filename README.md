# FitnessGym

A simple, modern gym management web application.

Two sides:

- **Customer App** — public homepage, plans, registration, member dashboard, digital membership card with QR check-in.
- **Admin Dashboard** — single admin account with full access to members, plans, payments, attendance, reports, settings.

## Tech Stack

- **Frontend:** React + Vite + TypeScript + Tailwind CSS + shadcn/ui
- **Backend:** Python + FastAPI + SQLAlchemy + Alembic
- **Database:** PostgreSQL
- **Auth:** JWT-based with secure password hashing (Argon2)
- **Email (local):** Mailpit
- **Local services:** Docker Compose

## Repository Layout

```
fitness-gym/
├── backend/          FastAPI application
├── frontend/         React + Vite + TypeScript app
├── docker-compose.yml
└── README.md
```

## Local Setup

### Prerequisites

- Docker + Docker Compose
- Node.js 20+
- Python 3.12+

### 1. Start local services (PostgreSQL + Mailpit)

```bash
docker compose up -d
```

This launches:
- PostgreSQL on `localhost:5432` (user `gym`, password `gym`, db `fitness_gym`)
- Mailpit SMTP on `localhost:1025`, web UI on `http://localhost:8025`

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

API: `http://localhost:8000`
OpenAPI docs: `http://localhost:8000/docs`

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

App: `http://localhost:5173`

## Development Phases

1. Foundation + Docker + frontend/backend setup
2. Database + authentication
3. Membership system
4. Payment system
5. Digital membership card + QR check-in
6. Admin dashboard
7. Customer dashboard
8. Notifications
9. Reports
10. Testing + final polish
