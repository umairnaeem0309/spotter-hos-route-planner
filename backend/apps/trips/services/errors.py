"""
Typed provider/domain errors for the routing and geocoding services.

Every error subclasses ``ApiError`` (a DRF ``APIException``), so a view can
raise one and the project's ``safe_exception_handler`` renders the canonical
error body with the correct HTTP status. Messages are always client-safe:
they never contain the API key, raw upstream payloads, or stack traces.

Status mapping:
- Invalid/blank address, no route found -> 400 (the client's input is at fault)
- Rate limited -> 503 (transient; retry later)
- Timeout, upstream failure, missing key -> 502 (bad gateway / misconfig)
"""
from __future__ import annotations

from rest_framework import status

from apps.trips.api.exceptions import ApiError


class ProviderError(ApiError):
    """Base class for routing/geocoding provider failures."""

    status_code = status.HTTP_502_BAD_GATEWAY
    default_code = "provider_error"
    default_detail = "The routing provider could not complete the request."


class ProviderNotConfiguredError(ProviderError):
    """Raised when the ORS API key is missing.

    This is a server misconfiguration, not a client error; the message never
    reveals key contents (there are none) and does not echo configuration.
    """

    status_code = status.HTTP_502_BAD_GATEWAY
    default_code = "provider_not_configured"
    default_detail = (
        "The routing service is not configured. Please try again later."
    )


class GeocodingError(ProviderError):
    """A geocoding lookup failed at the provider level."""

    default_code = "geocoding_error"
    default_detail = "The location could not be resolved."


class AddressNotFoundError(GeocodingError):
    """The provider returned no match for an address (client input problem)."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "address_not_found"
    default_detail = "No matching location was found for the address provided."


class RoutingError(ProviderError):
    """A directions request failed at the provider level."""

    default_code = "routing_error"
    default_detail = "A route could not be generated."


class NoRouteFoundError(RoutingError):
    """No drivable route exists between the requested points."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "no_route_found"
    default_detail = "No drivable route was found between the given locations."


class ProviderRateLimitedError(ProviderError):
    """The provider returned HTTP 429 (transient)."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_code = "provider_rate_limited"
    default_detail = (
        "The routing service is temporarily busy. Please try again shortly."
    )


class ProviderTimeoutError(ProviderError):
    """The provider did not respond within the configured timeout."""

    status_code = status.HTTP_502_BAD_GATEWAY
    default_code = "provider_timeout"
    default_detail = "The routing service timed out. Please try again."


class ProviderUnavailableError(ProviderError):
    """The provider returned a 5xx or an otherwise unusable response."""

    status_code = status.HTTP_502_BAD_GATEWAY
    default_code = "provider_unavailable"
    default_detail = "The routing service is currently unavailable."
