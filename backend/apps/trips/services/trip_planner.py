"""
Trip-planning orchestration.

Ties the provider clients, the pure HOS scheduler, and route-progress mapping
together into the documented ``POST /api/trips/plan/`` response. Kept out of the
API view so the view stays a thin request/response adapter (ADR-003).
"""
from __future__ import annotations

import uuid
from datetime import datetime, time, timedelta, timezone

from apps.trips.services import geocoding, route_progress, routing
from apps.trips.services.hos_scheduler import ScheduleResult, plan_trip
from apps.trips.types import Route, TimelineEvent

# Static disclosure copy shown in the UI's "Calculation assumptions" panel.
ASSUMPTIONS: list[str] = [
    "Property-carrying commercial motor vehicle driver in interstate commerce.",
    "70-hour / 8-day cycle.",
    "Driver starts after at least 10 consecutive hours off duty.",
    "'Current cycle used' is total on-duty hours already used in the current "
    "70-hour cycle.",
    "Because only the cycle total (not the previous 8 individual days) is "
    "supplied, exact rolling recapture cannot be calculated; a conservative "
    "bucket of (70 - current cycle used) hours is used instead.",
    "A 34-hour restart is inserted when the conservative bucket is exhausted "
    "and driving remains.",
    "Pickup and drop-off each take 60 minutes, On Duty (Not Driving).",
    "Fueling is planned about every 900 route miles; each fuel stop is 30 "
    "minutes, On Duty (Not Driving), and satisfies the 30-minute break.",
    "Overnight resets use a 10-hour sleeper-berth period.",
    "No adverse-driving, short-haul, personal-conveyance, split-sleeper, or "
    "team-driver logic is applied.",
    "All schedule and log times use the trip-start timezone, even across "
    "timezone boundaries.",
]

_DEMO_DISCLAIMER = (
    "This is an assessment/demo trip planner, not a certified ELD or a "
    "legal-compliance product."
)
_CYCLE_DISCLAIMER = (
    "Cycle hours are modeled conservatively as (70 - current cycle used) "
    "because per-day history for the previous 8 days is not provided."
)


def _resolve_trip_start(trip_start: datetime | None) -> datetime:
    if trip_start is None:
        # Default: current time, timezone-aware (UTC). Callers seeking
        # reproducibility supply an explicit trip_start with an offset.
        return datetime.now(timezone.utc).replace(microsecond=0)
    if trip_start.tzinfo is None:
        return trip_start.replace(tzinfo=timezone.utc)
    return trip_start


def _event_to_dict(event: TimelineEvent) -> dict:
    return {
        "type": event.type.value,
        "duty_status": event.duty_status.value,
        "start_at": event.start_at,
        "end_at": event.end_at,
        "duration_minutes": event.duration_minutes,
        "distance_miles": round(event.distance_miles, 2),
        "coordinate": list(event.coordinate) if event.coordinate else None,
        "location_label": event.location_label,
        "description": event.description,
        "reason_code": event.reason_code,
    }


def _count_log_days(departure_iso: str, arrival_iso: str) -> int:
    dep = datetime.fromisoformat(departure_iso)
    arr = datetime.fromisoformat(arrival_iso)
    start_date = dep.date()
    end_date = arr.date()
    # An arrival exactly at midnight belongs to the day that just ended.
    if arr.timetz().replace(tzinfo=None) == time(0, 0) and end_date > start_date:
        end_date -= timedelta(days=1)
    return (end_date - start_date).days + 1


def _route_dict(
    route: Route, current_label: str, pickup_label: str, dropoff_label: str
) -> dict:
    waypoint_meta = [
        ("current", current_label),
        ("pickup", pickup_label),
        ("dropoff", dropoff_label),
    ]
    waypoints = []
    for (kind, label), coordinate in zip(waypoint_meta, route.waypoints):
        waypoints.append(
            {"type": kind, "label": label, "coordinate": list(coordinate)}
        )
    instructions = [
        {
            "text": step.instruction,
            "name": step.name,
            "distance_miles": round(step.distance_meters / 1609.344, 2),
            "duration_minutes": int(round(step.duration_seconds / 60.0)),
        }
        for step in route.all_steps
    ]
    return {
        "geometry": {
            "type": "LineString",
            "coordinates": [list(c) for c in route.geometry],
        },
        "waypoints": waypoints,
        "instructions": instructions,
    }


def _build_warnings(schedule: ScheduleResult) -> list[str]:
    warnings = [_DEMO_DISCLAIMER, _CYCLE_DISCLAIMER]
    if schedule.cycle_restart_count > 0:
        warnings.append(
            "A 34-hour restart was scheduled because the modeled 70-hour cycle "
            "was exhausted while driving remained."
        )
    return warnings


def build_trip_plan(
    *,
    current_location: str,
    pickup_location: str,
    dropoff_location: str,
    current_cycle_used_hours: float,
    trip_start: datetime | None = None,
    reverse_geocode_stops: bool = True,
) -> dict:
    """Produce the full trip-plan response payload.

    Raises the typed provider/validation errors from the service layer; the
    view's safe exception handler renders them.
    """
    start = _resolve_trip_start(trip_start)

    current = geocoding.geocode(current_location)
    pickup = geocoding.geocode(pickup_location)
    dropoff = geocoding.geocode(dropoff_location)

    route = routing.get_route(
        [current.coordinate, pickup.coordinate, dropoff.coordinate]
    )

    legs = route_progress.build_driving_legs(route)
    schedule = plan_trip(legs, start, current_cycle_used_hours)

    route_progress.apply_route_progress(
        schedule.events,
        route,
        current_label=current.label,
        pickup_label=pickup.label,
        dropoff_label=dropoff.label,
        reverse_geocode_stops=reverse_geocode_stops,
    )

    number_of_log_days = _count_log_days(schedule.departure_at, schedule.arrival_at)

    return {
        "trip_id": str(uuid.uuid4()),
        "input": {
            "current_location": current_location,
            "pickup_location": pickup_location,
            "dropoff_location": dropoff_location,
            "current_cycle_used_hours": current_cycle_used_hours,
            "trip_start": start.isoformat(),
        },
        "summary": {
            "total_distance_miles": round(route.total_distance_miles, 2),
            "raw_driving_minutes": schedule.raw_driving_minutes,
            "compliant_trip_minutes": schedule.compliant_trip_minutes,
            "departure_at": schedule.departure_at,
            "arrival_at": schedule.arrival_at,
            "number_of_log_days": number_of_log_days,
            "fuel_stop_count": schedule.fuel_stop_count,
            "rest_break_count": schedule.rest_break_count,
            "overnight_rest_count": schedule.overnight_rest_count,
            "cycle_restart_count": schedule.cycle_restart_count,
        },
        "route": _route_dict(route, current.label, pickup.label, dropoff.label),
        "timeline": [_event_to_dict(e) for e in schedule.events],
        "daily_logs": [],  # populated in Phase 5
        "assumptions": ASSUMPTIONS,
        "warnings": _build_warnings(schedule),
    }
