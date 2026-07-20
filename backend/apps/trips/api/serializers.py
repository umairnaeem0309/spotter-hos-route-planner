"""
Request (de)serialization and field-level validation for the trip endpoint.

Validation rules (per the API contract):
- The three locations must be non-blank strings.
- ``current_cycle_used_hours`` is a number in [0, 70].
- ``trip_start`` is optional; when supplied it must be valid ISO-8601. The
  original UTC offset is preserved so the trip (and its logs) use the driver's
  intended local time base (ADR-006).
"""
from __future__ import annotations

from datetime import datetime

from rest_framework import serializers


class TripPlanRequestSerializer(serializers.Serializer):
    current_location = serializers.CharField(
        trim_whitespace=True, allow_blank=False, max_length=255
    )
    pickup_location = serializers.CharField(
        trim_whitespace=True, allow_blank=False, max_length=255
    )
    dropoff_location = serializers.CharField(
        trim_whitespace=True, allow_blank=False, max_length=255
    )
    current_cycle_used_hours = serializers.FloatField(min_value=0, max_value=70)
    # Parsed manually (see validate) to preserve the supplied UTC offset.
    trip_start = serializers.CharField(required=False, allow_blank=True)

    def validate_trip_start(self, value: str) -> datetime | None:
        if value is None or value.strip() == "":
            return None
        text = value.strip()
        # Accept a trailing "Z" (UTC) which datetime.fromisoformat rejects on
        # older Python; normalize it defensively.
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError as exc:
            raise serializers.ValidationError(
                "trip_start must be a valid ISO-8601 datetime."
            ) from exc
        return parsed
