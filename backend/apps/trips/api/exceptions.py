"""
Consistent, safe API error schema.

Every error response the API returns follows one shape so the frontend can
handle failures uniformly and no internal detail (stack traces, provider
payloads, secrets) ever leaks to the client:

    {
      "error": {
        "code": "validation_error",
        "message": "Human-readable, safe summary.",
        "details": { ... optional, field-level or structured ... }
      }
    }

The domain/provider error classes used from Phase 2 onward subclass
``ApiError`` so views can raise a typed error and the handler renders it
safely with the right HTTP status.
"""
from __future__ import annotations

from typing import Any

from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def error_body(
    code: str, message: str, details: Any | None = None
) -> dict[str, Any]:
    """Build the canonical error payload."""
    body: dict[str, Any] = {"error": {"code": code, "message": message}}
    if details is not None:
        body["error"]["details"] = details
    return body


class ApiError(APIException):
    """Base class for typed, client-safe API errors.

    Subclasses set ``status_code``, ``default_code``, and ``default_detail``.
    The message is always considered safe to show to the client; never place
    secrets or raw upstream payloads in it.
    """

    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "error"
    default_detail = "A request error occurred."


def safe_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """DRF exception handler that always returns the canonical error schema.

    Validation errors keep their field-level details; everything else is
    reduced to a safe code/message pair.
    """
    response = drf_exception_handler(exc, context)

    if response is None:
        # Unhandled exception: never leak internals.
        return Response(
            error_body(
                "internal_error",
                "An unexpected server error occurred.",
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # DRF field-validation errors (blank locations, out-of-range cycle hours,
    # bad ISO-8601 trip_start): preserve the field-level detail under
    # ``details`` so the frontend can show inline messages.
    if isinstance(exc, ValidationError):
        response.data = error_body(
            "validation_error",
            "The submitted data was invalid.",
            details=response.data,
        )
        return response

    # Every other APIException (including typed ApiError subclasses such as
    # address_not_found or no_route_found) keeps its own code and safe message,
    # regardless of HTTP status.
    code = getattr(exc, "default_code", None) or "error"
    detail = response.data.get("detail") if isinstance(response.data, dict) else None
    message = str(detail) if detail else "A request error occurred."
    response.data = error_body(code, message)
    return response
