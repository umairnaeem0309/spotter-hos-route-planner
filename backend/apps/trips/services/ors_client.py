"""
Low-level HTTP client for OpenRouteService (HeiGIT).

This is the ONLY place external ORS requests originate. It centralizes:
- reading the API key from settings (never hard-coded, never logged),
- an explicit request timeout,
- transport-level error mapping (timeout, connection, rate limit, 5xx),
- key-safe logging (query strings, which carry the Pelias ``api_key``, are
  stripped before anything is logged).

Endpoint-specific parsing (Pelias features, directions GeoJSON) lives in
``geocoding.py`` and ``routing.py``; they interpret 2xx/4xx bodies. This module
raises only for transport failures and clearly transient/server errors.
"""
from __future__ import annotations

import logging
from urllib.parse import urlsplit, urlunsplit

import requests
from django.conf import settings

from .errors import (
    ProviderNotConfiguredError,
    ProviderRateLimitedError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)

logger = logging.getLogger("apps.trips.ors")


def get_api_key() -> str:
    """Return the configured ORS API key or raise if it is missing."""
    key = (getattr(settings, "ORS_API_KEY", "") or "").strip()
    if not key:
        # Do not reveal configuration internals to the client.
        raise ProviderNotConfiguredError()
    return key


def _safe_url(url: str) -> str:
    """Strip the query string so a logged URL can never leak ``api_key``."""
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def build_url(path: str) -> str:
    """Join the configured ORS base URL with an endpoint path."""
    base = settings.ORS_BASE_URL.rstrip("/")
    return f"{base}/{path.lstrip('/')}"


def send(
    method: str,
    url: str,
    *,
    params: dict | None = None,
    json: dict | None = None,
    headers: dict | None = None,
) -> requests.Response:
    """Perform an ORS request and map transport/transient errors to typed ones.

    Raises:
        ProviderTimeoutError: the request exceeded the configured timeout.
        ProviderRateLimitedError: the provider returned HTTP 429.
        ProviderUnavailableError: connection failure or a 5xx response.

    Returns the raw ``requests.Response`` for 2xx and other 4xx responses so
    callers can parse success bodies and interpret client-input failures
    (e.g. no address match, no route).
    """
    timeout = float(getattr(settings, "ORS_REQUEST_TIMEOUT_SECONDS", 15.0))
    try:
        response = requests.request(
            method,
            url,
            params=params,
            json=json,
            headers=headers,
            timeout=timeout,
        )
    except requests.Timeout as exc:
        logger.warning("ORS request timed out: %s %s", method, _safe_url(url))
        raise ProviderTimeoutError() from exc
    except requests.RequestException as exc:
        # Never log the exception repr; it can echo the full URL with the key.
        logger.warning(
            "ORS request failed (%s): %s %s",
            type(exc).__name__,
            method,
            _safe_url(url),
        )
        raise ProviderUnavailableError() from exc

    if response.status_code == 429:
        logger.warning("ORS rate limited: %s %s", method, _safe_url(url))
        raise ProviderRateLimitedError()
    if 500 <= response.status_code < 600:
        logger.warning(
            "ORS upstream error %s: %s %s",
            response.status_code,
            method,
            _safe_url(url),
        )
        raise ProviderUnavailableError()

    return response
