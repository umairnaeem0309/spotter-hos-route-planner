"""
Tests that typed provider/domain errors render through the safe exception
handler as the canonical error body with the correct HTTP status and code.
"""
from __future__ import annotations

import pytest
from rest_framework.exceptions import ValidationError

from apps.trips.api.exceptions import error_body, safe_exception_handler
from apps.trips.services.errors import (
    AddressNotFoundError,
    NoRouteFoundError,
    ProviderNotConfiguredError,
    ProviderRateLimitedError,
    ProviderTimeoutError,
)


def test_error_body_shape():
    body = error_body("x_code", "A message", details={"field": ["bad"]})
    assert body == {
        "error": {
            "code": "x_code",
            "message": "A message",
            "details": {"field": ["bad"]},
        }
    }


def test_error_body_omits_details_when_none():
    assert error_body("x", "y") == {"error": {"code": "x", "message": "y"}}


@pytest.mark.parametrize(
    ("exc", "expected_status", "expected_code"),
    [
        (AddressNotFoundError(), 400, "address_not_found"),
        (NoRouteFoundError(), 400, "no_route_found"),
        (ProviderRateLimitedError(), 503, "provider_rate_limited"),
        (ProviderTimeoutError(), 502, "provider_timeout"),
        (ProviderNotConfiguredError(), 502, "provider_not_configured"),
    ],
)
def test_typed_errors_render_with_status_and_code(exc, expected_status, expected_code):
    response = safe_exception_handler(exc, {})
    assert response is not None
    assert response.status_code == expected_status
    assert response.data["error"]["code"] == expected_code
    # Message is present and safe (no key, no stack trace).
    message = response.data["error"]["message"]
    assert isinstance(message, str) and message
    assert "Traceback" not in message


def test_validation_error_preserves_field_details():
    exc = ValidationError({"current_cycle_used_hours": ["Must be <= 70."]})
    response = safe_exception_handler(exc, {})
    assert response is not None
    assert response.status_code == 400
    assert response.data["error"]["code"] == "validation_error"
    assert response.data["error"]["details"] == {
        "current_cycle_used_hours": ["Must be <= 70."]
    }


def test_unhandled_exception_becomes_safe_500():
    response = safe_exception_handler(RuntimeError("boom: secret detail"), {})
    assert response is not None
    assert response.status_code == 500
    assert response.data["error"]["code"] == "internal_error"
    assert "secret" not in response.data["error"]["message"]
