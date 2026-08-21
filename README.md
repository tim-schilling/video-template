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

This project can be deployed to a PythonAnywhere
[Beginner account](https://www.pythonanywhere.com/registration/register/beginner/)
(free, no credit card) via
[`django-simple-deploy`](https://django-simple-deploy.readthedocs.io/) and the
[`dsd-pythonanywhere`](https://github.com/caktus/dsd-pythonanywhere) plugin, both
already in the `dev` dependency group.

**Prerequisites:**

- The [`op` CLI](https://developer.1password.com/docs/cli/) installed and signed in.
- A 1Password item named "Python Anywhere" (in the `Private` vault) with a
  `username` field (your PythonAnywhere username) and an `api-token` field (from
  [Account → API Token](https://help.pythonanywhere.com/pages/GettingYourAPIToken)).
  `.env.pythonanywhere` references these as `op://Private/Python Anywhere/username`
  and `op://Private/Python Anywhere/api-token` — update it if your vault/item/field
  names differ. It holds only `op://` references, not secrets, so it's safe to commit.
- A GitHub (or similar) remote for this repo — the plugin pushes your default
  branch and clones it on PythonAnywhere.
- Stay logged in to PythonAnywhere in your default browser during deployment; the
  plugin opens a browser console it needs a human session to start.

**Beginner-tier constraints already accounted for:**

- No Postgres/MySQL access, so `DATABASES` falls back to SQLite via
  `DATABASE_URL` when nothing else is configured — see `config/settings.py`.
- No always-on/scheduled tasks, so `TASKS` switches to `django_tasks`'s
  `ImmediateBackend` (runs synchronously in the request) when the plugin's
  `ON_PYTHONANYWHERE` env var is set, instead of queuing to a `db_worker` that
  can never run.
- No custom domains — the app is served from `<username>.pythonanywhere.com`.

**Deploying:**

```sh
just deploy-pythonanywhere-plan   # generates a plan without touching PythonAnywhere
just deploy-pythonanywhere        # --automate-all: pushes, deploys, and opens the site
```

Both recipes regenerate `requirements.txt` from `uv.lock` first — PythonAnywhere's
setup script `pip install`s from it, not `uv.lock`. `django-simple-deploy` also
appends `dsd-pythonanywhere`, `django-simple-deploy`, `python-dotenv`, and
`dj-database-url` to `requirements.txt` when it runs; `dsd-pythonanywhere` and
`django-simple-deploy` aren't needed at runtime (only to run `manage.py deploy`),
and installing the former from its git dependency may not work against
PythonAnywhere's outbound-access allowlist, so remove those two lines from
`requirements.txt` before committing/pushing.

After a deploy, check the PythonAnywhere-specific block the plugin appends to the
bottom of `config/settings.py`: its own `DEBUG = os.getenv("DEBUG") == "TRUE"`
overrides ours and runs *after* the `if not DEBUG:` security block above, so set
`DEBUG=FALSE` in the `.env` file it creates on PythonAnywhere (not the `TRUE`
default from its setup script) — otherwise the site runs with `DEBUG=True` in
production.

`dsd-pythonanywhere` is still in active development and its README doesn't yet
recommend it for real deployments — review what it changes before relying on it.

## Testing & linting

```sh
just test   # pytest, DJANGO_SETTINGS_MODULE=config.settings
just lint   # pre-commit run --all-files
just format # ruff format
```

## Layout

- `config/` — project settings, URLs, WSGI/ASGI entrypoints
- `forum/` — the example app (models, views, forms, tasks, templates, tests)
