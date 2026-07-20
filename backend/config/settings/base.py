"""
Base Django settings shared by all environments.

Environment-specific behaviour (safe development defaults vs. strict
production requirements) lives in ``development.py`` and ``production.py``.
Values are read from the environment via ``django-environ`` so that no secret
is ever hard-coded or committed. See ``.env.example`` for the supported keys.
"""
from __future__ import annotations

from pathlib import Path

import environ

# backend/config/settings/base.py -> parents[2] == backend/
BASE_DIR = Path(__file__).resolve().parents[2]

env = environ.Env()

# Load a local .env file when present. It is git-ignored and only used for
# local development; production supplies real values through the environment.
_ENV_FILE = BASE_DIR / ".env"
if _ENV_FILE.exists():
    environ.Env.read_env(str(_ENV_FILE))


# --- Core toggles -----------------------------------------------------------

# DEBUG defaults to False here; development settings override it to True.
DEBUG = env.bool("DEBUG", default=False)

ALLOWED_HOSTS: list[str] = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])


# --- Applications -----------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    # Local
    "apps.trips",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    # CSRF middleware is retained for defense in depth. DRF marks its API views
    # csrf_exempt, so the token-free cross-origin SPA POST is unaffected.
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

X_FRAME_OPTIONS = "DENY"

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": []},
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# --- Database ---------------------------------------------------------------

# The assessment does not require persistence (ADR-009). A lightweight SQLite
# database keeps Django's checks/migrations happy without adding a service.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- Internationalization ---------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# --- Static files -----------------------------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# --- Django REST Framework --------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    # This is a stateless, unauthenticated public API (no user accounts are in
    # scope). Disabling auth avoids depending on django.contrib.auth and its
    # AnonymousUser, which DRF would otherwise resolve on every request.
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "UNAUTHENTICATED_USER": None,
    "EXCEPTION_HANDLER": "apps.trips.api.exceptions.safe_exception_handler",
}


# --- CORS -------------------------------------------------------------------

# React (Vite) origin(s) allowed to call the API. Values come from the
# environment so deployments configure their own hosted frontend origin.
FRONTEND_URL = env.str("FRONTEND_URL", default="http://localhost:5173")
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=[FRONTEND_URL] if FRONTEND_URL else [],
)
CORS_ALLOW_CREDENTIALS = False


# --- OpenRouteService (used from Phase 2 onward) ----------------------------

# Read here so the whole app has a single source of truth. Never logged, never
# returned in an API response, never exposed to the browser.
ORS_API_KEY = env.str("ORS_API_KEY", default="")
ORS_BASE_URL = env.str("ORS_BASE_URL", default="https://api.heigit.org")
ORS_REQUEST_TIMEOUT_SECONDS = env.float("ORS_REQUEST_TIMEOUT_SECONDS", default=15.0)


# --- Logging ----------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "standard"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}
