import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

ON_PYTHONANYWHERE = os.environ.get("ON_PYTHONANYWHERE", "") == "TRUE"

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
# Fails closed: an unset DEBUG (e.g. a deploy target that forgot to set it)
# gets production behavior, not an accidentally-exposed debug page.
DEBUG = os.environ.get("DEBUG", "False") == "True"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_tasks",
    "django_tasks_db",
    "django_prodserver",
    "forum",
]

if DEBUG:
    # Only needed to run `manage.py deploy`; safe to drop after configuring a target.
    INSTALLED_APPS.append("django_simple_deploy")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}

LOGIN_REDIRECT_URL = "topic-list"
LOGOUT_REDIRECT_URL = "topic-list"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO"),
    },
}

if not DEBUG:
    SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "True") == "True"
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "60"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    CSRF_TRUSTED_ORIGINS = [
        origin
        for origin in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")
        if origin
    ]

if ON_PYTHONANYWHERE:
    # The Beginner tier has no always-on process to run `db_worker`, so tasks
    # run synchronously in the request instead of sitting unprocessed in the queue.
    TASKS = {"default": {"BACKEND": "django_tasks.backends.immediate.ImmediateBackend"}}
else:
    TASKS = {
        "default": {
            "BACKEND": "django_tasks_db.DatabaseBackend",
            "QUEUES": ["default"],
        }
    }

PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.servers.gunicorn.GunicornServer",
        "ARGS": {"bind": "0.0.0.0:8000"},
    },
    "worker": {
        "BACKEND": "django_prodserver.backends.workers.django_tasks.DjangoTasksWorker",
        "ARGS": {},
    },
}


# PythonAnywhere settings.
import os  # noqa: E402

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

if os.getenv("ON_PYTHONANYWHERE"):
    import dj_database_url

    DEBUG = os.getenv("DEBUG") == "TRUE"
    SECRET_KEY = os.getenv("SECRET_KEY")

    try:
        ALLOWED_HOSTS.append("*")
    except NameError:
        ALLOWED_HOSTS = ["*"]

    DATABASES = {
        "default": dj_database_url.config(),
    }

    STATIC_ROOT = os.path.join(BASE_DIR, "static")


# PythonAnywhere settings.
import os  # noqa: E402

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

if os.getenv("ON_PYTHONANYWHERE"):
    import dj_database_url

    DEBUG = os.getenv("DEBUG") == "TRUE"
    SECRET_KEY = os.getenv("SECRET_KEY")

    try:
        ALLOWED_HOSTS.append("*")
    except NameError:
        ALLOWED_HOSTS = ["*"]

    DATABASES = {
        "default": dj_database_url.config(),
    }

    STATIC_ROOT = os.path.join(BASE_DIR, "static")


# PythonAnywhere settings.
import os  # noqa: E402

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

if os.getenv("ON_PYTHONANYWHERE"):
    import dj_database_url

    DEBUG = os.getenv("DEBUG") == "TRUE"
    SECRET_KEY = os.getenv("SECRET_KEY")

    try:
        ALLOWED_HOSTS.append("*")
    except NameError:
        ALLOWED_HOSTS = ["*"]

    DATABASES = {
        "default": dj_database_url.config(),
    }

    STATIC_ROOT = os.path.join(BASE_DIR, "static")
