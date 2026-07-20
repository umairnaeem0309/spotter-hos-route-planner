"""
Integration tests for POST /api/trips/plan/.

External geocoding/routing is mocked, so these run without a live ORS key and
without network access. They assert the response contract, field-level
validation, and provider-failure mapping to the canonical error schema.
"""
from __future__ import annotations

from unittest import mock

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.trips.services.errors import (
    AddressNotFoundError,
    NoRouteFoundError,
    ProviderUnavailableError,
)
from apps.trips.types import GeocodedLocation, Route, RouteSegment, RouteStep

_COORDS = {
    "Chicago, IL": (-87.63, 41.88),
    "Indianapolis, IN": (-86.16, 39.77),
    "Nashville, TN": (-86.78, 36.16),
}


def _fake_geocode(address: str) -> GeocodedLocation:
    coord = _COORDS.get(address, (-87.0, 40.0))
    return GeocodedLocation(query=address, label=address, coordinate=coord)


def _fake_route() -> Route:
    geometry = (
        (-87.63, 41.88),
        (-86.16, 39.77),
        (-86.78, 36.16),
    )
    seg0 = RouteSegment(
        289682.0, 10800.0, (RouteStep("Head south", 289682.0, 10800.0, (0, 1), "I-65"),)
    )
    seg1 = RouteSegment(
        434523.0, 16200.0, (RouteStep("Continue", 434523.0, 16200.0, (1, 2), "I-65"),)
    )
    return Route(
        geometry=geometry,
        segments=(seg0, seg1),
        waypoints=geometry,
        total_distance_meters=724205.0,
        total_duration_seconds=27000.0,
    )


@pytest.fixture()
def client() -> APIClient:
    return APIClient()


@pytest.fixture()
def valid_payload() -> dict:
    return {
        "current_location": "Chicago, IL",
        "pickup_location": "Indianapolis, IN",
        "dropoff_location": "Nashville, TN",
        "current_cycle_used_hours": 5,
        "trip_start": "2026-07-20T08:00:00-05:00",
    }


def _mock_providers():
    return (
        mock.patch(
            "apps.trips.services.trip_planner.geocoding.geocode",
            side_effect=_fake_geocode,
        ),
        mock.patch(
            "apps.trips.services.trip_planner.routing.get_route",
            return_value=_fake_route(),
        ),
        mock.patch(
            "apps.trips.services.route_progress.geocoding.reverse_geocode",
            return_value=None,
        ),
    )


def _post(client: APIClient, payload: dict):
    p1, p2, p3 = _mock_providers()
    with p1, p2, p3:
        return client.post("/api/trips/plan/", payload, format="json")


# --------------------------------------------------------------------------- #
# Success
# --------------------------------------------------------------------------- #


def test_plan_returns_full_contract(client, valid_payload):
    response = _post(client, valid_payload)
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    for key in (
        "trip_id",
        "input",
        "summary",
        "route",
        "timeline",
        "daily_logs",
        "assumptions",
        "warnings",
    ):
        assert key in body

    summary = body["summary"]
    for key in (
        "total_distance_miles",
        "raw_driving_minutes",
        "compliant_trip_minutes",
        "departure_at",
        "arrival_at",
        "number_of_log_days",
        "fuel_stop_count",
        "rest_break_count",
        "overnight_rest_count",
        "cycle_restart_count",
    ):
        assert key in summary


def test_plan_summary_values(client, valid_payload):
    body = _post(client, valid_payload).json()
    summary = body["summary"]
    # ~450 miles, 7.5 h raw driving.
    assert 445 < summary["total_distance_miles"] < 455
    assert summary["raw_driving_minutes"] == 450
    # Short trip: one day, no overnight rest, no restart.
    assert summary["number_of_log_days"] == 1
    assert summary["overnight_rest_count"] == 0
    assert summary["cycle_restart_count"] == 0
    assert summary["fuel_stop_count"] == 0


def test_plan_includes_pickup_and_dropoff(client, valid_payload):
    body = _post(client, valid_payload).json()
    types = [e["type"] for e in body["timeline"]]
    assert "pickup" in types and "dropoff" in types
    pickup = next(e for e in body["timeline"] if e["type"] == "pickup")
    dropoff = next(e for e in body["timeline"] if e["type"] == "dropoff")
    assert pickup["duration_minutes"] == 60
    assert dropoff["duration_minutes"] == 60
    assert pickup["duty_status"] == "ON_DUTY_NOT_DRIVING"


def test_route_geometry_and_instructions(client, valid_payload):
    body = _post(client, valid_payload).json()
    route = body["route"]
    assert route["geometry"]["type"] == "LineString"
    assert len(route["geometry"]["coordinates"]) >= 2
    assert len(route["waypoints"]) == 3
    assert route["waypoints"][0]["type"] == "current"
    assert len(route["instructions"]) >= 1


def test_daily_logs_empty_until_phase5(client, valid_payload):
    body = _post(client, valid_payload).json()
    assert body["daily_logs"] == []


def test_trip_start_defaults_when_omitted(client, valid_payload):
    valid_payload.pop("trip_start")
    response = _post(client, valid_payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["input"]["trip_start"]


def test_no_api_key_or_secret_in_response(client, valid_payload):
    body = _post(client, valid_payload)
    text = body.content.decode()
    assert "ORS_API_KEY" not in text
    assert "Authorization" not in text


# --------------------------------------------------------------------------- #
# Validation (field-level 400s)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("field", ["current_location", "pickup_location", "dropoff_location"])
def test_blank_location_is_rejected(client, valid_payload, field):
    valid_payload[field] = "   "
    response = _post(client, valid_payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert field in body["error"]["details"]


@pytest.mark.parametrize("value", [-1, 71, 100])
def test_cycle_hours_out_of_range_rejected(client, valid_payload, value):
    valid_payload["current_cycle_used_hours"] = value
    response = _post(client, valid_payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["error"]["code"] == "validation_error"


def test_invalid_trip_start_rejected(client, valid_payload):
    valid_payload["trip_start"] = "not-a-date"
    response = _post(client, valid_payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert "trip_start" in body["error"]["details"]


# --------------------------------------------------------------------------- #
# Provider-failure mapping
# --------------------------------------------------------------------------- #


def test_address_not_found_maps_to_400(client, valid_payload):
    with mock.patch(
        "apps.trips.services.trip_planner.geocoding.geocode",
        side_effect=AddressNotFoundError(),
    ):
        response = client.post("/api/trips/plan/", valid_payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["error"]["code"] == "address_not_found"


def test_no_route_maps_to_400(client, valid_payload):
    with mock.patch(
        "apps.trips.services.trip_planner.geocoding.geocode",
        side_effect=_fake_geocode,
    ), mock.patch(
        "apps.trips.services.trip_planner.routing.get_route",
        side_effect=NoRouteFoundError(),
    ):
        response = client.post("/api/trips/plan/", valid_payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["error"]["code"] == "no_route_found"


def test_provider_unavailable_maps_to_502(client, valid_payload):
    with mock.patch(
        "apps.trips.services.trip_planner.geocoding.geocode",
        side_effect=_fake_geocode,
    ), mock.patch(
        "apps.trips.services.trip_planner.routing.get_route",
        side_effect=ProviderUnavailableError(),
    ):
        response = client.post("/api/trips/plan/", valid_payload, format="json")
    assert response.status_code == status.HTTP_502_BAD_GATEWAY
    assert response.json()["error"]["code"] == "provider_unavailable"
