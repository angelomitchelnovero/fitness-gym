# FitnessGym

A modern gym management web application. Customers sign up, pick a plan, pay,
walk in with a QR code. Admins run the floor, see reports, send reminders.

## Tech Stack

- **Frontend:** React 18 + Vite 5 + TypeScript 5 + Tailwind CSS 3 + shadcn-style components, React Query, React Router 6.
- **Backend:** Python 3.12+ · FastAPI · SQLAlchemy 2 · Alembic · Argon2 · JWT (HS256).
- **Database:** PostgreSQL 16 via `psycopg`.
- **Notifications:** Pluggable `NotificationChannel` (logging for local, SMTP for prod).
- **Email in dev:** [Mailpit](https://github.com/axllent/mailpit) — SMTP at `:1025`, UI at `:8025`.

## Repository Layout

```
fitness-gym/
├── backend/                   FastAPI app
│   ├── app/
│   │   ├── api/                routers + endpoint modules
│   │   ├── core/               config, security, deps
│   │   ├── db/                 Base, session
│   │   ├── models/             SQLAlchemy models
│   │   ├── schemas/            Pydantic response/request shapes
│   │   ├── services/           payment, checkin, notification, reports, ...
│   │   └── main.py             FastAPI factory
│   ├── alembic/                migrations
│   ├── tests/                  pytest
│   └── pyproject.toml
├── frontend/                   React app
│   ├── src/
│   │   ├── pages/              one .tsx per route
│   │   ├── components/         presentational + ui/
│   │   ├── lib/                api client, query hooks, utils
│   │   ├── types/              TS shapes mirroring backend schemas
│   │   └── App.tsx             router + admin layout
│   └── package.json
└── docker-compose.yml         postgres + mailpit
```

## Local Setup

### Prerequisites
- Docker + Docker Compose
- Node.js 20+
- Python 3.12+

### 1. Local services

```bash
docker compose up -d
```
Starts:
- **Postgres** on `localhost:5432` (user `gym`, password `gym`, db `fitness_gym`)
- **Mailpit** SMTP `:1025` + web UI at <http://localhost:8025>

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env             # edit JWT_SECRET
# create the 'admin' role etc. and run migrations:
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

API: `http://localhost:8000` · OpenAPI: `http://localhost:8000/docs`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

App: `http://localhost:5173`. The dev server proxies API calls to the FastAPI
default (`VITE_API_BASE_URL`, defaults to `/api/v1`).

### Useful one-offs

```bash
# seed an admin user (role promotion via DB is left to scripts/seed_admin.py)
.venv/bin/python scripts/seed_admin.py

# ad-hoc smoke against the live server
.venv/bin/python scripts/smoke_phase9.py

# tests
.venv/bin/pytest -q             # backend
npm run typecheck && npm run lint && npm run build    # frontend
```

## Features by Phase

| #  | Feature                                     | Primary paths |
|----|----------------------------------------------|----------------|
| 1  | Monorepo + Docker + FastAPI + Vite skeleton | — |
| 2  | Postgres, Alembic, JWT auth, Argon2, RBAC    | `/auth/*`, `/users` |
| 3  | Plans + memberships (purchase / renew / cancel) | `/plans`, `/memberships` |
| 4  | Mock payment provider, check-out flow, status transitions | `/payments/*` |
| 5  | Digital card JWT, anti-replay QR scan, history | `/checkin/*` |
| 6  | Admin dashboard: KPIs + recent activity      | `/admin/dashboard` |
| 7  | Customer dashboard: hero card, spend, QR, recent visits | `/dashboard` |
| 8  | Notifications: payment receipt, check-in confirmation, expiry reminder | `/notifications`, `/admin/notifications/expire-soon` |
| 9  | Reports: revenue by period, retention + churn, popular plans | `/admin/reports` |
| 10 | This README + deployment doc + final smoke   | — |

## API Map (versioned at `/api/v1`)

| Group         | Routes                                                                                       |
|---------------|----------------------------------------------------------------------------------------------|
| Auth          | `POST /auth/register`, `POST /auth/login`, `GET /auth/me`, `POST /auth/change-password`    |
| Plans         | `GET /plans`, `POST /plans/admin`, `GET /plans/admin/{id}`, `PATCH /plans/admin/{id}`      |
| Memberships   | `POST /memberships`, `GET /memberships/me`, `POST /memberships/{id}/cancel`, `/renew`, admin list/expiring |
| Payments      | `POST /payments/checkout`, `POST /payments/{id}/verify`, `GET /payments/me`, admin list     |
| Check-in      | `GET /checkin/card`, `POST /checkin/scan`, `GET /checkin/me`, admin list                    |
| Notifications | `GET /notifications/me`, admin `POST /admin/notifications/expire-soon`                     |
| Reports       | `GET /admin/reports?period=day|week|month&bucket=day|week`                                  |
| Customer      | `GET /dashboard/me`                                                                          |
| Admin         | `GET /admin/dashboard`                                                                       |

## Security Notes

- **JWT_SECRET** must be a long random string in non-dev envs.
  `JWT_SECRET=<64-byte secret>`. Generate with:
  ```python
  import secrets; print(secrets.token_urlsafe(64))
  ```
- Passwords are Argon2-hashed; tokens are signed (`HS256`); admin-only endpoints
  rely on the FastAPI `require_admin` dependency.
- Notifications are **fire-and-forget** at the call site: a send failure never
  blocks a successful payment or check-in.
- Anti-replay on QR tokens uses a `qr_token_uses` row keyed on `jti`, written
  before commit.
- SMTP is optional; the default `NOTIFICATION_CHANNEL=logging` records sends
  to stdout so local development works without external mail.

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for production notes.
