# School MVP

Multi-tenant school management system. Django + PostgreSQL + HTMX + Materialize/Bootstrap 5, with Celery/Redis for background work and a basic PWA shell.

## Requirements

- Python 3.10+
- PostgreSQL 13+
- Redis 6+ (Celery broker/result backend). If you're stuck on an older Redis build (5.x, no `HELLO`/RESP3 support), keep `redis==4.6.0` pinned in `requirements.txt` — newer `redis-py` versions fail to connect to it.

Node.js/npm is only needed if you're updating the vendored copy of htmx under `static/vendor/htmx.min.js` (see `package.json`); it's not required to run the app, since there is no CSS build step — Materialize is checked into `static/materialize/vendor/` directly.

## Setup

```bash
python -m venv venv
venv/Scripts/activate        # venv\Scripts\activate.bat on cmd.exe
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in real values:

```bash
cp .env.example .env
```

Required variables: `SECRET_KEY`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`. Generate a secret key with:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Create the database (name must match `DB_NAME`):

```sql
CREATE DATABASE school_mvp_db;
```

Run migrations and collect static files:

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

Create the global Super Admin (manages schools via `/admin/`):

```bash
python manage.py createsuperuser
```

Run the dev server:

```bash
python manage.py runserver
```

- `/admin/` — Super Admin: create/deactivate schools, manage everything.
- `/accounts/login/` — School Admin / Teacher / Staff login, redirects to `/dashboard/`.

## Tests

```bash
python manage.py test
```

Covers tenant isolation (cross-school data access is blocked at both the queryset and view layer), RBAC (each role's permitted/denied actions), the Excel import validator, and the audit logging integration.

## Background tasks (Celery)

Redis must be running and reachable at `REDIS_URL`.

```bash
celery -A core worker --loglevel=info    # Linux/macOS
celery -A core worker --loglevel=info --pool=solo   # Windows

celery -A core beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

Periodic tasks are stored in the database (`django_celery_beat`), not in a static `CELERY_BEAT_SCHEDULE` dict, so they're editable from `/admin/` under "Periodic tasks" without a redeploy. A daily audit-log retention job (`audit.tasks.purge_stale_audit_logs`, runs at 02:00, controlled by `AUDIT_LOG_RETENTION_DAYS` in `.env`) is created automatically by the `audit` app's migrations.

## Multi-school vs single-school deployment

By default (`SINGLE_SCHOOL_MODE=False`), the Super Admin creates and manages schools through `/admin/`.

For a single-school deployment, set `SINGLE_SCHOOL_MODE=True` and provision the one school plus its first admin with:

```bash
python manage.py bootstrap_school --name "Example School" --code EXS001 \
  --admin-username principal --admin-password "change-me" --admin-email admin@example.com
```

Values can also come from `.env` (`SCHOOL_NAME`, `SCHOOL_CODE`, `SCHOOL_ADMIN_USERNAME`, `SCHOOL_ADMIN_PASSWORD`, `SCHOOL_ADMIN_EMAIL`) instead of flags. The command is idempotent — running it again reuses the existing school/admin instead of duplicating them, and refuses to run at all if `SINGLE_SCHOOL_MODE` is off.

## PWA

`static/manifest.json` and the service worker (served at `/sw.js`, not under `/static/`, so its scope covers the whole app) are already wired into `base.html`. The service worker only caches the static app shell (CSS/JS/icons) — it never caches HTML or HTMX responses, since those carry per-tenant data that must always come from the network. To test installability, open the app in Chrome/Edge over `http://localhost:8000` or any HTTPS origin and use "Install app" from the address bar.

If you change any static assets, bump `CACHE_NAME` in `templates/sw.js` so returning users don't keep stale cached files.

## Production settings

Three settings modules under `core/settings/`: `base.py` (shared), `dev.py`, `prod.py`. Select one via `DJANGO_SETTINGS_MODULE` in `.env` (defaults to `core.settings.dev`).

`core.settings.prod` additionally requires/uses:

- `ALLOWED_HOSTS` (required, no default)
- `CSRF_TRUSTED_ORIGINS` (comma-separated, needed if serving over HTTPS behind a proxy)
- `EMAIL_HOST` / `EMAIL_PORT` / `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` for real email delivery

It also turns on `SECURE_SSL_REDIRECT`, HSTS, secure/HttpOnly/SameSite cookies, and `X_FRAME_OPTIONS=DENY`. Static files are served via WhiteNoise with manifest-based cache busting — run `collectstatic` as part of your deploy.

Run `python manage.py check --deploy` against your real production `.env` before going live.

## Project layout

- `core/` — Django project config (settings split, root urls, Celery app)
- `common/` — tenant-aware base manager/queryset/model, shared view mixins, form helpers, `bootstrap_school` command
- `permissions/` — RBAC: role → permission registry, decorators/mixins for views
- `schools/` — School (tenant) model, dashboard, school profile
- `accounts/` — custom User model, login, school-scoped user management
- `academics/` — academic years, classes, sections, streams (all school-defined)
- `staff/` — staff records and the activate-to-create-login flow
- `students/` — student records, academic mapping, Excel import
- `audit/` — audit log model/service, login signal hooks, retention task

## Roles

- **Super Admin** — global, Django admin only (`is_superuser`), manages schools.
- **School Admin** — full management of their own school: profile, users, staff, academics, students, audit log.
- **Teacher** — manages students within their own school.
- **Staff** — dashboard access only in this MVP; no management permissions by default.

Every protected view checks permissions server-side (`permissions.mixins.PermissionRequiredMixin` / `permissions.decorators.permission_required`) and every tenant-scoped queryset goes through `common.managers.TenantQuerySet.for_school()` — nav links hiding actions is a convenience, not the enforcement.
