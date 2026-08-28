# Deployment

This guide covers what you need to put FitnessGym in front of real users.

## 1. Build artifacts

### Backend

The backend is a standard FastAPI app — any WSGI/ASGI host works. For a
self-contained image, use a multi-stage Dockerfile:

```dockerfile
FROM python:3.12-slim AS build
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir ".[prod]"

FROM python:3.12-slim
WORKDIR /app
COPY --from=build /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .
COPY scripts ./scripts
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "app.main:app"]
```

`pip install -e ".[dev]"` (used locally) already pulls the production deps.

### Frontend

```bash
cd frontend
npm install
npm run build
```

Static output lands in `frontend/dist`. Serve it with any static host
(nginx, Caddy, Cloudflare Pages, S3+CloudFront). Configure the same
origin to reverse-proxy `/api` to the backend:

```
location /api/  { proxy_pass http://backend:8000; }
```

Set `VITE_API_BASE_URL` at build time. For same-origin deployments, leave
the default (`/api/v1`).

## 2. Required environment variables

Backend reads from `.env` / process env via `pydantic-settings`. Required
in production:

| Var                              | Notes                                                   |
|----------------------------------|---------------------------------------------------------|
| `APP_ENV=production`             | toggles OpenAPI docs off                                 |
| `DATABASE_URL`                   | `postgresql+psycopg://user:pass@host:5432/db`           |
| `JWT_SECRET`                     | **Required.** Random 64-byte string                    |
| `JWT_ALGORITHM`                  | default `HS256`                                         |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`| default 60                                              |
| `CORS_ORIGINS`                   | comma-separated list of frontend origins                |
| `FRONTEND_URL`                   | absolute origin used in email links                     |
| `SMTP_HOST/PORT/USER/PASSWORD`   | for `NOTIFICATION_CHANNEL=smtp` (Phase 8)               |
| `SMTP_FROM_EMAIL`, `SMTP_FROM_NAME` | envelope from                                           |
| `NOTIFICATION_CHANNEL`           | `logging` (default) or `smtp`                           |
| `MEMBERSHIP_EXPIRY_REMINDER_DAYS`| default 7                                               |

Anything else (API prefix, app name, version) can stay at defaults.

## 3. Migrations

Set the `DATABASE_URL` and run before first boot, and on every release:

```bash
alembic upgrade head
```

The Alembic env reads the same env-var config as the app — no second file
to maintain. To regenerate migrations after a model change:

```bash
alembic revision --autogenerate -m "what changed"
# review the file under alembic/versions/ — autogenerate is a draft
alembic upgrade head   # verify it applies cleanly
```

## 4. Running

- **ASGI:** `gunicorn -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 app.main:app`
- **Dev:** `uvicorn app.main:app --reload --port 8000`
- **Workers:** 1–2 × CPU is plenty for a gym-sized workload; tighten
  `keep-alive` if fronted by nginx.

Put the app behind a TLS-terminating proxy (nginx, Caddy, Cloudflare) and
allow only `/health` and `/docs` if you want OpenAPI exposed publicly.

## 5. Notifications

`NOTIFICATION_CHANNEL` selects the runtime strategy:

- `logging` — sends go to stdout (`logging` channel). Use in production only
  if downstream log shipping handles the consumer.
- `smtp` — uses `smtplib` with the env-var SMTP settings above. To plug in
  SendGrid/Postmark, point `SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/`SMTP_PASSWORD`
  at them.

For SMS / push, subclass `app.services.notifications.base.NotificationChannel`
and register it via `register_channel("name", cls)`, then set
`NOTIFICATION_CHANNEL=your-name`.

## 6. Database

- Run Postgres 14+ (16 tested).
- Set a generous `statement_timeout` (e.g. 10s) to insulate the API from
  runaway reports.
- Back up nightly. `pg_dump --schema-only` for a quick schema diff; full
  dumps are small for gym-scale data.

## 7. Observability

There is no built-in tracing. Recommended:

- `/health` for liveness; it returns 200 with `{"status": "ok"}`.
- Front the API with nginx and ship its access logs.
- Postgres slow-query log on statements over 1s.

## 8. Seed an admin

The repo does not ship a CLI for admin onboarding (it is intentionally a
short step, and the user already exists once the first admin signs in
manually). To bootstrap from a shell:

```bash
.venv/bin/python scripts/seed_admin.py
```
Reads `ADMIN_EMAIL` / `ADMIN_PASSWORD` from env, default
`admin@example.com` / `change-me`. Use `--rotate` to reset an existing
admin's password.

## 9. Upgrade checklist

1. Build new image, tag it (`v0.x.y`).
2. Drain traffic (your orchestration system handles this).
3. Run `alembic upgrade head` against the prod DB (with a quick
   `select 1` smoke first).
4. Roll out new pods with a previous-version fallback ready.
5. Verify `/health` and `/api/v1/admin/dashboard` (with admin token).
6. Keep the previous image for at least one release cycle.
