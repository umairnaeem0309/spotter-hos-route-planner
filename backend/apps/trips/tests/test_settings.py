"""Configuration-safety tests.

These verify that production settings fail loudly on insecure configuration
and that development/test settings expose safe defaults. They import the
settings modules in isolation so a misconfiguration is caught before deploy.
"""
from __future__ import annotations

import importlib

import pytest


def _reload_production(monkeypatch: pytest.MonkeyPatch, **env: str):
    """Import config.settings.production with a controlled environment."""
    for key in (
        "DJANGO_SECRET_KEY",
        "ALLOWED_HOSTS",
        "DEBUG",
        "SECURE_SSL_REDIRECT",
    ):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    module = importlib.import_module("config.settings.production")
    return importlib.reload(module)


def test_production_rejects_missing_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(RuntimeError, match="DJANGO_SECRET_KEY"):
        _reload_production(monkeypatch, ALLOWED_HOSTS="example.com")


def test_production_rejects_placeholder_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(RuntimeError, match="DJANGO_SECRET_KEY"):
        _reload_production(
            monkeypatch,
            DJANGO_SECRET_KEY="replace-with-a-long-random-secret",
            ALLOWED_HOSTS="example.com",
        )


def test_production_rejects_insecure_prefixed_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(RuntimeError, match="DJANGO_SECRET_KEY"):
        _reload_production(
            monkeypatch,
            DJANGO_SECRET_KEY="django-insecure-anything",
            ALLOWED_HOSTS="example.com",
        )


def test_production_requires_allowed_hosts(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(RuntimeError, match="ALLOWED_HOSTS"):
        _reload_production(
            monkeypatch,
            DJANGO_SECRET_KEY="a-sufficiently-strong-production-secret-value",
        )


def test_production_accepts_valid_config(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _reload_production(
        monkeypatch,
        DJANGO_SECRET_KEY="a-sufficiently-strong-production-secret-value",
        ALLOWED_HOSTS="example.com,api.example.com",
    )
    assert module.DEBUG is False
    assert module.ALLOWED_HOSTS == ["example.com", "api.example.com"]
    assert module.SESSION_COOKIE_SECURE is True


def test_debug_parsed_as_bool(monkeypatch: pytest.MonkeyPatch) -> None:
    """DEBUG must be parsed safely: the string 'False' is not truthy."""
    import environ

    env = environ.Env()
    monkeypatch.setenv("DEBUG", "False")
    assert env.bool("DEBUG") is False
    monkeypatch.setenv("DEBUG", "0")
    assert env.bool("DEBUG") is False
    monkeypatch.setenv("DEBUG", "true")
    assert env.bool("DEBUG") is True


@pytest.fixture(autouse=True)
def _restore_test_settings():
    """Reload the test settings after each test that reloaded production.

    Reloading production.py mutates the shared module object; restore the
    active test settings so later tests are unaffected.
    """
    yield
    importlib.reload(importlib.import_module("config.settings.test"))
