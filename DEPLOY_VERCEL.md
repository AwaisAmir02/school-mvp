# Deploying to Vercel with Neon Postgres

This is a demo deployment. Celery/Redis background tasks (audit log retention, scheduled jobs) will not run on Vercel — that is expected and does not need to be fixed for this deployment.

## 1. Create the Neon database

1. Create a project at neon.tech and copy its connection string. It looks like:
   `postgres://USER:PASSWORD@ep-xxxx.region.aws.neon.tech/DBNAME?sslmode=require`
2. Split that string into the pieces you'll need below: `DB_USER`, `DB_PASSWORD`, `DB_HOST` (the `ep-xxxx...neon.tech` part), `DB_NAME`, and `DB_PORT` (`5432`).

## 2. Set environment variables in the Vercel dashboard

Go to your Vercel project → Settings → Environment Variables and add:

| Variable | Required | Notes |
|---|---|---|
| `SECRET_KEY` | Yes | Generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `ALLOWED_HOSTS` | Yes | Your Vercel domain(s), comma-separated, e.g. `your-app.vercel.app` |
| `CSRF_TRUSTED_ORIGINS` | Yes | Must include the scheme, e.g. `https://your-app.vercel.app` — without this, login and every other POST form will fail with a CSRF error, since Vercel serves over HTTPS behind a proxy |
| `DB_NAME` | Yes | From the Neon connection string |
| `DB_USER` | Yes | From the Neon connection string |
| `DB_PASSWORD` | Yes | From the Neon connection string |
| `DB_HOST` | Yes | From the Neon connection string |
| `DB_PORT` | Yes | `5432` |
| `DB_SSLMODE` | No | Already defaults to `require`, which is what Neon needs. Only set this if Neon ever asks for something stricter, e.g. `verify-full` |
| `DJANGO_SETTINGS_MODULE` | No | `api/index.py` already defaults this to `core.settings.prod` |
| `SINGLE_SCHOOL_MODE` | No | Defaults to `False` |
| `TIME_ZONE` | No | Defaults to `UTC` |
| `AUDIT_LOG_RETENTION_DAYS` | No | Defaults to `365`. Irrelevant here since the retention task needs Celery Beat, which isn't running on Vercel |
| `EMAIL_HOST` / `EMAIL_PORT` / `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | No | Only needed if you want real outbound email from the demo; leave unset otherwise |

## 3. Configure the Vercel build command

Vercel's Python function only ships the code you commit — it does not run `collectstatic` for you, and the deployed filesystem is read-only at request time, so static files must already exist in `staticfiles/` before the function is packaged.

In Vercel dashboard → Settings → Build & Development Settings, set:

- **Install Command**: `pip install -r requirements.txt`
- **Build Command**: `python manage.py collectstatic --noinput`

This runs with the same environment variables set above, so `manage.py` can load `core.settings.prod` and reach the Neon database for the checks Django performs during `collectstatic`.

## 4. First deploy

Push to the branch Vercel is watching, or run `vercel --prod` from the project root. Vercel will install dependencies, run `collectstatic`, and deploy `api/index.py` behind the catch-all route in `vercel.json`.

## 5. Run migrations and create the first admin (run locally, pointed at Neon)

Vercel serverless functions don't give you a persistent shell, so run these from your own machine against the same Neon database:

```bash
export DJANGO_SETTINGS_MODULE=core.settings.prod
export SECRET_KEY=<same value as in Vercel>
export ALLOWED_HOSTS=your-app.vercel.app
export CSRF_TRUSTED_ORIGINS=https://your-app.vercel.app
export DB_NAME=<neon db name>
export DB_USER=<neon user>
export DB_PASSWORD=<neon password>
export DB_HOST=<neon host>
export DB_PORT=5432

python manage.py migrate
python manage.py createsuperuser
```

On Windows PowerShell, use `$env:VAR = "value"` instead of `export`.

After this, log in at `https://your-app.vercel.app/admin/` with the superuser you just created.

## 6. After every future deploy

Any new migration needs the same local-against-Neon step:

```bash
DJANGO_SETTINGS_MODULE=core.settings.prod python manage.py migrate
```

Static asset changes are picked up automatically the next time Vercel runs its Build Command.
