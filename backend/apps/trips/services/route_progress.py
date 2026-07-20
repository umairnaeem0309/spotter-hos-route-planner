"""
Route-progress mapping: bridge between the provider ``Route`` and the pure
HOS scheduler, and placement of scheduled events onto the route geometry.

Two responsibilities (ADR-007):
1. ``build_driving_legs`` converts a ``Route`` (meters/seconds) into the
   scheduler's ``DrivingLeg`` list (miles/integer-minutes), tagging the leg to
   the pickup and the final leg to the drop-off.
2. ``apply_route_progress`` maps each scheduled event's cumulative route
   distance to an approximate ``[lon, lat]`` on the route LineString and
   attaches a human label (exact for waypoints; reverse-geocoded best-effort
   for generated stops; a formatted lat/lon fallback otherwise). Generated fuel
   points are labeled as planned points, never asserted to be real facilities.
"""
from __future__ import annotations

import logging
import math

from apps.trips.types import (
    Coordinate,
    DrivingLeg,
    EventType,
    Route,
    TimelineEvent,
)

from . import geocoding
from .errors import ProviderError

logger = logging.getLogger("apps.trips.route_progress")

_METERS_PER_MILE = 1609.344
_EARTH_RADIUS_MILES = 3958.7613


def _meters_to_miles(meters: float) -> float:
    return meters / _METERS_PER_MILE


def _seconds_to_minutes(seconds: float) -> int:
    return int(round(seconds / 60.0))


def build_driving_legs(route: Route) -> list[DrivingLeg]:
    """Convert route segments into scheduler driving legs.

    For a current -> pickup -> drop-off route the provider returns one segment
    per waypoint pair. The final leg ends in DROPOFF; every earlier leg ends in
    PICKUP (this app has exactly one intermediate stop).
    """
    segments = route.segments
    legs: list[DrivingLeg] = []
    if not segments:
        # Degenerate provider response: fall back to a single drop-off leg.
        legs.append(
            DrivingLeg(
                distance_miles=_meters_to_miles(route.total_distance_meters),
                duration_minutes=_seconds_to_minutes(route.total_duration_seconds),
                end_event=EventType.DROPOFF,
            )
        )
        return legs

    last = len(segments) - 1
    for index, segment in enumerate(segments):
        end_event = EventType.DROPOFF if index == last else EventType.PICKUP
        legs.append(
            DrivingLeg(
                distance_miles=_meters_to_miles(segment.distance_meters),
                duration_minutes=_seconds_to_minutes(segment.duration_seconds),
                end_event=end_event,
            )
        )
    return legs


def _haversine_miles(a: Coordinate, b: Coordinate) -> float:
    lon1, lat1 = math.radians(a[0]), math.radians(a[1])
    lon2, lat2 = math.radians(b[0]), math.radians(b[1])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * _EARTH_RADIUS_MILES * math.asin(min(1.0, math.sqrt(h)))


def _cumulative_miles(geometry: tuple[Coordinate, ...]) -> list[float]:
    cum = [0.0]
    for i in range(1, len(geometry)):
        cum.append(cum[-1] + _haversine_miles(geometry[i - 1], geometry[i]))
    return cum


def _interpolate(
    geometry: tuple[Coordinate, ...], cum: list[float], target_miles: float
) -> Coordinate:
    if not geometry:
        return (0.0, 0.0)
    if len(geometry) == 1 or target_miles <= 0:
        return geometry[0]
    total = cum[-1]
    if target_miles >= total:
        return geometry[-1]
    # Find the segment containing target_miles.
    lo, hi = 0, len(cum) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if cum[mid] < target_miles:
            lo = mid + 1
        else:
            hi = mid
    i = max(1, lo)
    seg_len = cum[i] - cum[i - 1]
    frac = 0.0 if seg_len == 0 else (target_miles - cum[i - 1]) / seg_len
    (lon1, lat1), (lon2, lat2) = geometry[i - 1], geometry[i]
    return (lon1 + (lon2 - lon1) * frac, lat1 + (lat2 - lat1) * frac)


def _format_coordinate(coordinate: Coordinate) -> str:
    lon, lat = coordinate
    return f"{lat:.4f}, {lon:.4f}"


def _safe_reverse_geocode(coordinate: Coordinate) -> str | None:
    try:
        return geocoding.reverse_geocode(coordinate)
    except ProviderError:
        # Reverse geocoding is best-effort; never let it fail trip planning.
        logger.info("Reverse geocode unavailable for a generated stop")
        return None


def apply_route_progress(
    events: list[TimelineEvent],
    route: Route,
    *,
    current_label: str,
    pickup_label: str,
    dropoff_label: str,
    reverse_geocode_stops: bool = True,
) -> None:
    """Attach coordinates and labels to every scheduled event in place.

    Waypoint events (first position, pickup, drop-off) use exact resolved
    coordinates/labels. Other stops are interpolated along the route; fuel is
    labeled as a planned point; rest/sleeper/restart stops are reverse-geocoded
    best-effort with a formatted lat/lon fallback.
    """
    geometry = route.geometry
    cum = _cumulative_miles(geometry)
    geom_total = cum[-1] if cum else 0.0
    scheduled_total = max(
        (e.meta.get("end_distance_miles", 0.0) for e in events), default=0.0
    )
    scale = (geom_total / scheduled_total) if scheduled_total > 0 else 1.0

    waypoints = route.waypoints
    current_wp = waypoints[0] if len(waypoints) >= 1 else None
    pickup_wp = waypoints[1] if len(waypoints) >= 3 else None
    dropoff_wp = waypoints[-1] if len(waypoints) >= 2 else None

    first_driving_seen = False

    for event in events:
        start_miles = float(event.meta.get("start_distance_miles", 0.0))
        coordinate = _interpolate(geometry, cum, start_miles * scale)

        if event.type is EventType.PICKUP:
            if pickup_wp is not None:
                coordinate = pickup_wp
            event.location_label = pickup_label
        elif event.type is EventType.DROPOFF:
            if dropoff_wp is not None:
                coordinate = dropoff_wp
            event.location_label = dropoff_label
        elif event.type is EventType.DRIVING and not first_driving_seen:
            first_driving_seen = True
            if current_wp is not None:
                coordinate = current_wp
            event.location_label = current_label
        elif event.type is EventType.FUEL:
            event.location_label = "Planned fuel stop along route"
        else:
            label = (
                _safe_reverse_geocode(coordinate) if reverse_geocode_stops else None
            )
            event.location_label = label or _format_coordinate(coordinate)

        event.coordinate = (round(coordinate[0], 6), round(coordinate[1], 6))
