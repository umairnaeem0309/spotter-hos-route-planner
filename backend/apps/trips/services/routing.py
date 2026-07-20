"""
Heavy-goods-vehicle routing via OpenRouteService directions.

Requests a ``driving-hgv`` GeoJSON route through the ordered waypoints
current -> pickup -> drop-off and normalizes the response into the framework
-free ``Route`` type. Called only from Django; the API key travels in the
``Authorization`` header and is never logged or returned.

Endpoint: {base}/openrouteservice/v2/directions/driving-hgv/geojson
"""
from __future__ import annotations

import logging
from collections.abc import Sequence

from apps.trips.types import (
    Coordinate,
    Route,
    RouteSegment,
    RouteStep,
)

from .errors import NoRouteFoundError, RoutingError
from .ors_client import build_url, get_api_key, send

logger = logging.getLogger("apps.trips.routing")

_DIRECTIONS_PATH = "openrouteservice/v2/directions/driving-hgv/geojson"


def _coord_pair(value: object) -> Coordinate:
    if (
        not isinstance(value, (list, tuple))
        or len(value) < 2
        or not all(isinstance(c, (int, float)) for c in value[:2])
    ):
        raise RoutingError()
    return (float(value[0]), float(value[1]))


def _parse_steps(raw_steps: object) -> tuple[RouteStep, ...]:
    steps: list[RouteStep] = []
    if not isinstance(raw_steps, list):
        return ()
    for step in raw_steps:
        if not isinstance(step, dict):
            continue
        wp = step.get("way_points") or [0, 0]
        try:
            way_points = (int(wp[0]), int(wp[1]))
        except (TypeError, ValueError, IndexError):
            way_points = (0, 0)
        steps.append(
            RouteStep(
                instruction=str(step.get("instruction", "")),
                distance_meters=float(step.get("distance", 0.0)),
                duration_seconds=float(step.get("duration", 0.0)),
                way_points=way_points,
                name=str(step.get("name", "") or ""),
            )
        )
    return tuple(steps)


def _parse_segments(raw_segments: object) -> tuple[RouteSegment, ...]:
    segments: list[RouteSegment] = []
    if not isinstance(raw_segments, list):
        return ()
    for segment in raw_segments:
        if not isinstance(segment, dict):
            continue
        segments.append(
            RouteSegment(
                distance_meters=float(segment.get("distance", 0.0)),
                duration_seconds=float(segment.get("duration", 0.0)),
                steps=_parse_steps(segment.get("steps")),
            )
        )
    return tuple(segments)


def get_route(waypoints: Sequence[Coordinate]) -> Route:
    """Request an HGV route through the ordered waypoints.

    Args:
        waypoints: ordered ``[lon, lat]`` coordinates, at least two
            (current -> pickup -> drop-off = three for this app).

    Raises:
        NoRouteFoundError: no drivable route exists (HTTP 400 to the client).
        RoutingError / ProviderError: malformed response or provider failure.
    """
    points = [_coord_pair(wp) for wp in waypoints]
    if len(points) < 2:
        raise RoutingError()

    body = {
        "coordinates": [[lon, lat] for (lon, lat) in points],
        "instructions": True,
        "units": "m",
    }
    headers = {
        "Authorization": get_api_key(),
        "Content-Type": "application/json",
        "Accept": "application/geo+json, application/json",
    }
    response = send("POST", build_url(_DIRECTIONS_PATH), json=body, headers=headers)

    if response.status_code >= 400:
        # A 4xx from directions with valid geocoded points means the route
        # itself could not be produced (unroutable / exceeds limits).
        logger.info("Routing provider returned status %s", response.status_code)
        raise NoRouteFoundError()

    try:
        data = response.json()
    except ValueError as exc:
        raise RoutingError() from exc

    features = data.get("features") if isinstance(data, dict) else None
    if not features:
        raise NoRouteFoundError()

    feature = features[0]
    geometry = feature.get("geometry") or {}
    raw_coords = geometry.get("coordinates")
    if not isinstance(raw_coords, list) or not raw_coords:
        raise NoRouteFoundError()
    line = tuple(_coord_pair(c) for c in raw_coords)

    props = feature.get("properties") or {}
    segments = _parse_segments(props.get("segments"))
    summary = props.get("summary") or {}
    total_distance = float(
        summary.get("distance", sum(s.distance_meters for s in segments))
    )
    total_duration = float(
        summary.get("duration", sum(s.duration_seconds for s in segments))
    )

    return Route(
        geometry=line,
        segments=segments,
        waypoints=tuple(points),
        total_distance_meters=total_distance,
        total_duration_seconds=total_duration,
    )
