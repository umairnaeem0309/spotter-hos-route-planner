"""
Shared domain types for the trips app.

These are plain, framework-free dataclasses/enums so the pure services
(geocoding, routing, HOS scheduler, route progress, daily-log builder) can be
unit-tested without Django request state. Coordinates are always
``[longitude, latitude]`` to match GeoJSON and OpenRouteService.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

# GeoJSON / ORS coordinate order is [longitude, latitude].
Coordinate = tuple[float, float]


class DutyStatus(str, Enum):
    """The four FMCSA duty statuses used on a daily log."""

    OFF_DUTY = "OFF_DUTY"
    SLEEPER_BERTH = "SLEEPER_BERTH"
    DRIVING = "DRIVING"
    ON_DUTY_NOT_DRIVING = "ON_DUTY_NOT_DRIVING"


class EventType(str, Enum):
    """Timeline event categories emitted by the scheduler."""

    DRIVING = "driving"
    PICKUP = "pickup"
    DROPOFF = "dropoff"
    FUEL = "fuel"
    REST_BREAK = "rest_break"
    SLEEPER_BERTH = "sleeper_berth"
    CYCLE_RESTART = "cycle_restart"


@dataclass(frozen=True)
class GeocodedLocation:
    """A resolved address returned by the geocoding provider."""

    query: str
    label: str
    coordinate: Coordinate


@dataclass(frozen=True)
class RouteStep:
    """A single turn-by-turn instruction along a route segment.

    ``way_points`` holds the [start, end] indices into the segment/route
    geometry coordinate list, matching the ORS directions response.
    """

    instruction: str
    distance_meters: float
    duration_seconds: float
    way_points: tuple[int, int]
    name: str = ""


@dataclass(frozen=True)
class RouteSegment:
    """One leg of the route (e.g. current->pickup, pickup->drop-off)."""

    distance_meters: float
    duration_seconds: float
    steps: tuple[RouteStep, ...] = ()


@dataclass(frozen=True)
class Route:
    """Normalized routing-provider result.

    ``geometry`` is an ordered list of ``[lon, lat]`` coordinates
    (a GeoJSON LineString's coordinate array). ``waypoints`` are the ordered
    input stops (current, pickup, drop-off) as resolved coordinates.
    """

    geometry: tuple[Coordinate, ...]
    segments: tuple[RouteSegment, ...]
    waypoints: tuple[Coordinate, ...]
    total_distance_meters: float
    total_duration_seconds: float

    @property
    def total_distance_miles(self) -> float:
        return self.total_distance_meters / 1609.344

    @property
    def all_steps(self) -> tuple[RouteStep, ...]:
        steps: list[RouteStep] = []
        for segment in self.segments:
            steps.extend(segment.steps)
        return tuple(steps)


@dataclass
class TimelineEvent:
    """A single scheduled activity on the compliant trip timeline."""

    type: EventType
    duty_status: DutyStatus
    start_at: str  # ISO-8601, timezone-aware
    end_at: str  # ISO-8601, timezone-aware
    duration_minutes: int
    distance_miles: float = 0.0
    coordinate: Coordinate | None = None
    location_label: str = ""
    description: str = ""
    reason_code: str = ""  # machine-readable reason a stop was scheduled
    meta: dict = field(default_factory=dict)
