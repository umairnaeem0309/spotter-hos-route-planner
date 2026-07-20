"""
Provider-layer tests for geocoding, routing, and the low-level ORS client.

All external HTTP is mocked at ``requests.request`` so the suite never needs a
live ``ORS_API_KEY`` and never touches the network. Tests assert both success
parsing and every failure mode, plus key-safe logging behavior.
"""
from __future__ import annotations

from unittest import mock

import pytest
import requests
from django.test import override_settings

from apps.trips.services import geocoding, ors_client, routing
from apps.trips.services.errors import (
    AddressNotFoundError,
    NoRouteFoundError,
    ProviderNotConfiguredError,
    ProviderRateLimitedError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)

_FAKE_KEY = "test-fake-ors-key"


class FakeResponse:
    """Minimal stand-in for ``requests.Response``."""

    def __init__(self, status_code: int, payload: object = None, *, bad_json=False):
        self.status_code = status_code
        self._payload = payload
        self._bad_json = bad_json

    def json(self):
        if self._bad_json:
            raise ValueError("not json")
        return self._payload


def _patch_request(return_value=None, side_effect=None):
    """Patch the single point where ORS HTTP requests are issued."""
    return mock.patch.object(
        ors_client.requests,
        "request",
        return_value=return_value,
        side_effect=side_effect,
    )


# --------------------------------------------------------------------------- #
# Configuration / key handling
# --------------------------------------------------------------------------- #


@override_settings(ORS_API_KEY="")
def test_missing_key_raises_not_configured():
    with pytest.raises(ProviderNotConfiguredError):
        geocoding.geocode("Chicago, IL")


@override_settings(ORS_API_KEY=_FAKE_KEY)
def test_get_api_key_strips_whitespace():
    with override_settings(ORS_API_KEY="  spaced-key  "):
        assert ors_client.get_api_key() == "spaced-key"


def test_safe_url_strips_query_string():
    url = "https://api.heigit.org/pelias/v1/search?api_key=SECRET&text=Chicago"
    safe = ors_client._safe_url(url)
    assert "SECRET" not in safe
    assert safe == "https://api.heigit.org/pelias/v1/search"


# --------------------------------------------------------------------------- #
# Transport / transient error mapping (low-level client)
# --------------------------------------------------------------------------- #


@override_settings(ORS_API_KEY=_FAKE_KEY)
def test_timeout_maps_to_provider_timeout():
    with _patch_request(side_effect=requests.Timeout()):
        with pytest.raises(ProviderTimeoutError):
            geocoding.geocode("Chicago, IL")


@override_settings(ORS_API_KEY=_FAKE_KEY)
def test_connection_error_maps_to_unavailable():
    with _patch_request(side_effect=requests.ConnectionError()):
        with pytest.raises(ProviderUnavailableError):
            geocoding.geocode("Chicago, IL")


@override_settings(ORS_API_KEY=_FAKE_KEY)
def test_rate_limit_maps_to_rate_limited():
    with _patch_request(return_value=FakeResponse(429)):
        with pytest.raises(ProviderRateLimitedError):
            geocoding.geocode("Chicago, IL")


@override_settings(ORS_API_KEY=_FAKE_KEY)
def test_server_error_maps_to_unavailable():
    with _patch_request(return_value=FakeResponse(503)):
        with pytest.raises(ProviderUnavailableError):
            routing.get_route([(-87.6, 41.8), (-86.1, 39.7)])


# --------------------------------------------------------------------------- #
# Geocoding
# --------------------------------------------------------------------------- #

_GEOCODE_OK = {
    "features": [
        {
            "geometry": {"type": "Point", "coordinates": [-87.6298, 41.8781]},
            "properties": {"label": "Chicago, IL, USA"},
        }
    ]
}


@override_settings(ORS_API_KEY=_FAKE_KEY)
def test_geocode_success_parses_coordinate_and_label():
    with _patch_request(return_value=FakeResponse(200, _GEOCODE_OK)):
        result = geocoding.geocode("Chicago, IL")
    assert result.coordinate == (-87.6298, 41.8781)
    assert result.label == "Chicago, IL, USA"
    assert result.query == "Chicago, IL"


@override_settings(ORS_API_KEY=_FAKE_KEY)
def test_geocode_uses_query_as_label_fallback():
    payload = {"features": [{"geometry": {"coordinates": [1.0, 2.0]}, "properties": {}}]}
    with _patch_request(return_value=FakeResponse(200, payload)):
        result = geocoding.geocode("Nowhere")
    assert result.label == "Nowhere"


@override_settings(ORS_API_KEY=_FAKE_KEY)
def test_geocode_blank_address_raises_not_found():
    with pytest.raises(AddressNotFoundError):
        geocoding.geocode("   ")


@override_settings(ORS_API_KEY=_FAKE_KEY)
def test_geocode_empty_features_raises_not_found():
    with _patch_request(return_value=FakeResponse(200, {"features": []})):
        with pytest.raises(AddressNotFoundError):
            geocoding.geocode("Zzzznotreal")


@override_settings(ORS_API_KEY=_FAKE_KEY)
def test_geocode_4xx_raises_not_found():
    with _patch_request(return_value=FakeResponse(400, {"error": "bad"})):
        with pytest.raises(AddressNotFoundError):
            geocoding.geocode("bad input")


@override_settings(ORS_API_KEY=_FAKE_KEY)
def test_reverse_geocode_success():
    payload = {"features": [{"properties": {"label": "Springfield, MO"}}]}
    with _patch_request(return_value=FakeResponse(200, payload)):
        assert geocoding.reverse_geocode((-93.29, 37.20)) == "Springfield, MO"


@override_settings(ORS_API_KEY=_FAKE_KEY)
def test_reverse_geocode_missing_returns_none():
    with _patch_request(return_value=FakeResponse(200, {"features": []})):
        assert geocoding.reverse_geocode((-93.29, 37.20)) is None


@override_settings(ORS_API_KEY=_FAKE_KEY)
def test_reverse_geocode_4xx_returns_none():
    with _patch_request(return_value=FakeResponse(404, {})):
        assert geocoding.reverse_geocode((0.0, 0.0)) is None


# --------------------------------------------------------------------------- #
# Routing
# --------------------------------------------------------------------------- #

_ROUTE_OK = {
    "features": [
        {
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [-87.6298, 41.8781],
                    [-86.9, 40.5],
                    [-86.1581, 39.7684],
                ],
            },
            "properties": {
                "segments": [
                    {
                        "distance": 296000.0,
                        "duration": 12000.0,
                        "steps": [
                            {
                                "distance": 296000.0,
                                "duration": 12000.0,
                                "instruction": "Head south",
                                "name": "I-65 S",
                                "way_points": [0, 2],
                            }
                        ],
                    }
                ],
                "summary": {"distance": 296000.0, "duration": 12000.0},
            },
        }
    ]
}


@override_settings(ORS_API_KEY=_FAKE_KEY)
def test_route_success_parses_geometry_segments_and_totals():
    with _patch_request(return_value=FakeResponse(200, _ROUTE_OK)):
        route = routing.get_route([(-87.6298, 41.8781), (-86.1581, 39.7684)])
    assert len(route.geometry) == 3
    assert route.geometry[0] == (-87.6298, 41.8781)
    assert route.total_distance_meters == 296000.0
    assert route.total_duration_seconds == 12000.0
    assert len(route.segments) == 1
    steps = route.all_steps
    assert len(steps) == 1
    assert steps[0].instruction == "Head south"
    assert steps[0].way_points == (0, 2)
    # ~183.9 miles
    assert 183.0 < route.total_distance_miles < 184.5


@override_settings(ORS_API_KEY=_FAKE_KEY)
def test_route_sends_hgv_body_and_auth_header():
    with _patch_request(return_value=FakeResponse(200, _ROUTE_OK)) as m:
        routing.get_route([(-87.6298, 41.8781), (-86.1581, 39.7684)])
    _args, kwargs = m.call_args
    assert kwargs["headers"]["Authorization"] == _FAKE_KEY
    assert kwargs["json"]["coordinates"] == [[-87.6298, 41.8781], [-86.1581, 39.7684]]
    assert kwargs["json"]["instructions"] is True
    assert "driving-hgv" in _args[1]  # url is the second positional arg


@override_settings(ORS_API_KEY=_FAKE_KEY)
def test_route_empty_features_raises_no_route():
    with _patch_request(return_value=FakeResponse(200, {"features": []})):
        with pytest.raises(NoRouteFoundError):
            routing.get_route([(-87.6, 41.8), (-86.1, 39.7)])


@override_settings(ORS_API_KEY=_FAKE_KEY)
def test_route_4xx_raises_no_route():
    with _patch_request(return_value=FakeResponse(404, {"error": {"code": 2010}})):
        with pytest.raises(NoRouteFoundError):
            routing.get_route([(-87.6, 41.8), (-86.1, 39.7)])


@override_settings(ORS_API_KEY=_FAKE_KEY)
def test_route_requires_two_waypoints():
    from apps.trips.services.errors import RoutingError

    with pytest.raises(RoutingError):
        routing.get_route([(-87.6, 41.8)])
