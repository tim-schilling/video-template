# django-howto-template

A minimal Django project template for demonstrating Django how-to's. It ships with a
small example app — a forum with `Topic`s and flat, chronologically-ordered `Comment`s
(no categories, no comment threading) — and a set of modern tooling choices:

- [`uv`](https://docs.astral.sh/uv/) for dependency management
- [`just`](https://github.com/casey/just) as the task runner
- [`dj-database-url`](https://github.com/jazzband/dj-database-url) for database
  config, defaulting to a local SQLite file; point `DATABASE_URL` at Postgres
  (`docker-compose.yml` ships one) for a closer-to-production setup
- The Django Tasks framework (via [`django-tasks`](https://github.com/RealOrangeOne/django-tasks))
  with the [`django-tasks-db`](https://github.com/RealOrangeOne/django-tasks-db)
  database backend for background work
- [`django-prodserver`](https://github.com/nanorepublica/django-prodserver) for running
  the web (Gunicorn) and worker processes with a consistent management command
- `pre-commit` with a trimmed-down version of
  [django-msgspec's hooks](https://github.com/adamchainz/django-msgspec/blob/main/.pre-commit-config.yaml)
- `pytest` (via `pytest-django`) as the test runner, with tests written in plain
  `unittest` style (`django.test.TestCase` subclasses) and `factory_boy` for test data
- [`whitenoise`](https://whitenoise.readthedocs.io/) for serving static files from the
  Gunicorn process, with compressed, manifest-hashed storage
- A GitHub Actions workflow (`.github/workflows/ci.yml`) running `just test` and
  `just lint` against a Postgres service container on every push/PR

## Quickstart

```sh
cp .env.example .env
just install    # uv sync
just migrate     # creates db.sqlite3 by default
just superuser   # optional, to log in and create topics/comments
just run         # runserver at http://localhost:8000
```

To use Postgres locally instead of SQLite, run `just up` (starts
`docker-compose.yml`'s Postgres container) and set `DATABASE_URL` in `.env` — see
`.env.example`.

## Running tasks & the prod-style server

```sh
just worker   # runs django-tasks-db's db_worker via django-prodserver
just server   # runs gunicorn via django-prodserver
```

Creating a comment enqueues a `forum.tasks.notify_new_comment` task, processed by
whichever `db_worker` (started directly or via `just worker`) is running.

`just server` serves static files itself via WhiteNoise, so run `just collectstatic`
first (WhiteNoise reads from `STATIC_ROOT`, populated by `collectstatic`).

## Email

`MAILERS["default"]` uses the console backend, so anything sent (e.g. the
password-reset flow from `django.contrib.auth.urls`) is printed to stdout instead of
requiring real SMTP config. Swap it for a real backend before deploying anywhere
users need actual emails.

## Logging & production security settings

- `LOGGING` sends everything to a console handler at `DJANGO_LOG_LEVEL` (default
  `INFO`) — plays nicely with `docker logs`/platform log collectors.
- When `DEBUG=False`, a standard security block turns on `SECURE_SSL_REDIRECT`,
  secure session/CSRF cookies, HSTS (`SECURE_HSTS_SECONDS`, default `60`), and
  `SECURE_CONTENT_TYPE_NOSNIFF`, and reads `CSRF_TRUSTED_ORIGINS` from the
  environment. See `.env.example` for the relevant variables. None of this affects
  local dev, where `DEBUG=True`.

## Deploying to PythonAnywhere

Deploys to a free PythonAnywhere
[Beginner account](https://www.pythonanywhere.com/registration/register/beginner/)
via [`django-simple-deploy`](https://django-simple-deploy.readthedocs.io/) and the
[`dsd-pythonanywhere`](https://github.com/caktus/dsd-pythonanywhere) plugin (dev
dependencies). It's still in active development — review what it changes before
relying on it.

**Prerequisites:**

- The [`op` CLI](https://developer.1password.com/docs/cli/), signed in, with a
  "Python Anywhere" item (`Private` vault, per `.env.pythonanywhere`) holding
  `username` and `api-token` fields.
- A GitHub (or similar) remote for this repo — the plugin pushes to it and clones
  it on PythonAnywhere.
- Stay logged into PythonAnywhere in your default browser during deploy; the
  plugin opens a browser console that needs a human session to start.

**Deploying:**

```sh
just deploy-pythonanywhere-plan   # generates a plan without touching PythonAnywhere
just deploy-pythonanywhere        # --automate-all: pushes, deploys, and opens the site
```

Both recipes run `scripts/repair_pythonanywhere_deploy.py` afterward, which fixes
two things the plugin gets wrong: it pollutes `requirements.txt` with packages
only needed to run `manage.py deploy`, not the deployed app, and (with `--remote`,
used by `deploy-pythonanywhere`) it can leave the PythonAnywhere WSGI file
pointing at nothing. See the script's docstring for details.

After deploying, set `DEBUG=FALSE` in the PythonAnywhere `.env` file — the
plugin's setup script defaults it to `TRUE`, which would run production with
debug mode on.

Beginner-tier limits already handled in `config/settings.py`: SQLite fallback
when no `DATABASE_URL` is set, tasks run synchronously instead of queuing to a
worker, and the app is served from `<username>.pythonanywhere.com` (no custom
domains).

## Testing & linting

```sh
just test   # pytest, DJANGO_SETTINGS_MODULE=config.settings
just lint   # pre-commit run --all-files
just format # ruff format
```

## Layout

- `config/` — project settings, URLs, WSGI/ASGI entrypoints
- `forum/` — the example app (models, views, forms, tasks, templates, tests)
