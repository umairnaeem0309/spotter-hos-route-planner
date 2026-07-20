"""
Production settings: strict, fail-safe configuration.

Requires a real secret key and explicit host/origin allowlists. Refuses to
start with a missing or placeholder secret so a misconfigured deploy fails
loudly instead of shipping an insecure default.
"""
from __future__ import annotations

from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False

_PLACEHOLDER_SECRETS = {
    "",
    "replace-with-a-long-random-secret",
    "django-insecure-development-only-key-do-not-use-in-production",
}

SECRET_KEY = env.str("DJANGO_SECRET_KEY", default="")
if SECRET_KEY in _PLACEHOLDER_SECRETS or SECRET_KEY.startswith("django-insecure-"):
    raise RuntimeError(
        "DJANGO_SECRET_KEY must be set to a strong, non-placeholder value in "
        "production. Refusing to start with an insecure secret key."
    )

# No implicit host allowlist in production; it must be configured explicitly.
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
if not ALLOWED_HOSTS:
    raise RuntimeError(
        "ALLOWED_HOSTS must be configured explicitly in production."
    )

# HTTPS / security hardening. Render (and most PaaS) terminate TLS at a proxy
# and forward this header.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=60 * 60 * 24 * 30)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
