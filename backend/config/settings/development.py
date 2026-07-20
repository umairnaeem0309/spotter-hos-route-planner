"""
Development settings: safe, permissive defaults for local work.

Never used in production. A predictable insecure secret key is acceptable
here because DEBUG is on and the server is local-only.
"""
from __future__ import annotations

from .base import *  # noqa: F401,F403
from .base import env

DEBUG = env.bool("DEBUG", default=True)

# A non-secret development key. Production refuses to start with a placeholder
# like this (see production.py).
SECRET_KEY = env.str(
    "DJANGO_SECRET_KEY",
    default="django-insecure-development-only-key-do-not-use-in-production",
)

ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "0.0.0.0"]
)
