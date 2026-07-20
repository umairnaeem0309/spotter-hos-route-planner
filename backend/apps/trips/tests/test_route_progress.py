"""Unit tests for route-progress mapping (legs + coordinate placement)."""
from __future__ import annotations

from unittest import mock

from apps.trips.services import route_progress
from apps.trips.services.hos_scheduler import plan_trip
from apps.trips.types import (
    EventType,
    Route,
    RouteSegment,
    RouteStep,
)


def _route() -> Route:
    # A simple straight line current -> pickup -> drop-off.
    geometry = (
        (-87.63, 41.88),
        (-86.90, 40.80),
        (-86.16, 39.77),  # pickup
        (-86.47, 37.97),
        (-86.78, 36.16),  # drop-off
    )
    seg0 = RouteSegment(
        distance_meters=289682.0,  # ~180 mi
        duration_seconds=10800.0,  # 3 h
        steps=(RouteStep("Head south", 289682.0, 10800.0, (0, 2), "I-65 S"),),
    )
    seg1 = RouteSegment(
        distance_meters=434523.0,  # ~270 mi
        duration_seconds=16200.0,  # 4.5 h
        steps=(RouteStep("Continue south", 434523.0, 16200.0, (2, 4), "I-65 S"),),
    )
    return Route(
        geometry=geometry,
        segments=(seg0, seg1),
        waypoints=((-87.63, 41.88), (-86.16, 39.77), (-86.78, 36.16)),
        total_distance_meters=724205.0,
        total_duration_seconds=27000.0,
    )


def test_build_driving_legs_maps_segments():
    legs = route_progress.build_driving_legs(_route())
    assert len(legs) == 2
    assert legs[0].end_event is EventType.PICKUP
    assert legs[1].end_event is EventType.DROPOFF
    # ~180 mi, 180 min
    assert abs(legs[0].distance_miles - 180.0) < 0.5
    assert legs[0].duration_minutes == 180
    assert legs[1].duration_minutes == 270


def test_build_driving_legs_empty_segments_fallback():
    route = Route(
        geometry=((-87.0, 41.0), (-86.0, 40.0)),
        segments=(),
        waypoints=((-87.0, 41.0), (-86.0, 40.0)),
        total_distance_meters=160934.0,  # ~100 mi
        total_duration_seconds=6000.0,
    )
    legs = route_progress.build_driving_legs(route)
    assert len(legs) == 1
    assert legs[0].end_event is EventType.DROPOFF


def test_interpolate_midpoint():
    geometry = ((0.0, 0.0), (0.0, 1.0))  # ~69 mi north
    cum = route_progress._cumulative_miles(geometry)
    mid = route_progress._interpolate(geometry, cum, cum[-1] / 2)
    assert abs(mid[1] - 0.5) < 1e-6
    assert abs(mid[0] - 0.0) < 1e-6


def test_apply_route_progress_sets_waypoints_and_labels():
    route = _route()
    legs = route_progress.build_driving_legs(route)
    from datetime import datetime, timedelta, timezone

    start = datetime(2026, 7, 20, 8, 0, tzinfo=timezone(timedelta(hours=-6)))
    schedule = plan_trip(legs, start, 5.0)

    with mock.patch.object(
        route_progress.geocoding, "reverse_geocode", return_value=None
    ):
        route_progress.apply_route_progress(
            schedule.events,
            route,
            current_label="Chicago, IL",
            pickup_label="Indianapolis, IN",
            dropoff_label="Nashville, TN",
        )

    pickup = next(e for e in schedule.events if e.type is EventType.PICKUP)
    dropoff = next(e for e in schedule.events if e.type is EventType.DROPOFF)
    assert pickup.location_label == "Indianapolis, IN"
    assert pickup.coordinate == (-86.16, 39.77)
    assert dropoff.location_label == "Nashville, TN"
    assert dropoff.coordinate == (-86.78, 36.16)

    first_driving = next(e for e in schedule.events if e.type is EventType.DRIVING)
    assert first_driving.location_label == "Chicago, IL"
    assert first_driving.coordinate == (-87.63, 41.88)

    # Every event now has a coordinate assigned.
    assert all(e.coordinate is not None for e in schedule.events)
