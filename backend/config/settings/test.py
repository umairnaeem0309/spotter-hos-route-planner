"""
Test settings: deterministic configuration for the pytest suite.

Isolated from any local .env so tests never depend on developer machine state
or a live ORS key. Fixed, explicit values keep test runs reproducible in CI.
"""
from __future__ import annotations

from .base import *  # noqa: F401,F403

DEBUG = False
SECRET_KEY = "test-only-secret-key-not-used-anywhere-else"  # noqa: S105
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]

FRONTEND_URL = "http://localhost:5173"
CORS_ALLOWED_ORIGINS = ["http://localhost:5173"]

# Never rely on a real key in automated tests; providers are mocked.
ORS_API_KEY = ""

# Plain static storage in tests: no collectstatic/manifest is run, so the
# manifest-based production storage would warn about a missing manifest.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
