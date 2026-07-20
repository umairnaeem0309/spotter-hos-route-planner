"""
Daily-log construction.

Turns the immutable HOS timeline into one log per calendar day (in the
trip-start timezone), suitable for rendering on the supplied blank paper-log
template. Each day:

- splits any event crossing midnight into per-day segments (exact minutes;
  driving miles prorated across split driving segments),
- fills uncovered time with Off Duty so the four duty-status totals sum to
  exactly 1,440 minutes with no gaps or overlaps,
- reports per-day driving miles, remarks at each real status change, a modeled
  70-hour recap, and demo identity/vehicle metadata (flagged as demo).

Pure and deterministic: no HTTP/ORM/wall-clock dependency (ADR-003).
"""
from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Iterable

from apps.trips.types import DutyStatus, EventType, TimelineEvent

MINUTES_PER_DAY = 1440

_ON_DUTY_TYPES = {
    EventType.DRIVING,
    EventType.PICKUP,
    EventType.DROPOFF,
    EventType.FUEL,
}

# Demo metadata: the assessment does not collect these fields, so they are
# clearly-labeled placeholders (surfaced as such in the UI).
DEFAULT_METADATA = {
    "driver_name": "Assessment Driver",
    "carrier": "Spotter Assessment Carrier",
    "main_office": "Chicago, IL",
    "vehicle": "TRACTOR-001 / TRAILER-001",
    "shipping_document": "ASSESSMENT-LOAD",
    "is_demo": True,
}

_ACTIVITY_BY_TYPE = {
    EventType.DRIVING: "Began driving",
    EventType.PICKUP: "Pickup",
    EventType.DROPOFF: "Drop-off",
    EventType.FUEL: "Fueling (planned fuel stop)",
    EventType.REST_BREAK: "30-minute rest break",
    EventType.SLEEPER_BERTH: "Entered sleeper berth",
    EventType.CYCLE_RESTART: "Began 34-hour restart",
}


class _Segment:
    __slots__ = ("start", "end", "duty", "event_type", "miles", "label", "is_event_start")

    def __init__(self, start, end, duty, event_type, miles, label, is_event_start):
        self.start = start
        self.end = end
        self.duty = duty
        self.event_type = event_type
        self.miles = miles
        self.label = label
        self.is_event_start = is_event_start


def _parse(event: TimelineEvent) -> tuple[datetime, datetime]:
    return (
        datetime.fromisoformat(event.start_at),
        datetime.fromisoformat(event.end_at),
    )


def _minutes(delta: timedelta) -> int:
    return int(delta.total_seconds() // 60)


def _midnight(day, tzinfo) -> datetime:
    # Trip timezone is a fixed offset (from ISO parsing), so combine+tzinfo is
    # unambiguous across the day boundary.
    return datetime.combine(day, time(0, 0)).replace(tzinfo=tzinfo)


def _split_by_day(events: list[TimelineEvent]) -> dict:
    """Split events at midnight and bucket the resulting segments by date."""
    buckets: dict = {}
    for event in events:
        start, end = _parse(event)
        tzinfo = start.tzinfo
        total = _minutes(end - start)
        cursor = start
        while cursor < end:
            day = cursor.date()
            next_midnight = _midnight(day + timedelta(days=1), tzinfo)
            seg_end = min(end, next_midnight)
            seg_minutes = _minutes(seg_end - cursor)
            if event.type is EventType.DRIVING and total > 0:
                miles = event.distance_miles * (seg_minutes / total)
            else:
                miles = 0.0
            segment = _Segment(
                start=cursor,
                end=seg_end,
                duty=event.duty_status,
                event_type=event.type,
                miles=miles,
                label=event.location_label,
                is_event_start=(cursor == start),
            )
            buckets.setdefault(day, []).append(segment)
            cursor = seg_end
    return buckets


def _date_range(first, last) -> Iterable:
    current = first
    while current <= last:
        yield current
        current += timedelta(days=1)


def _fill_day(day, segments: list[_Segment], tzinfo) -> list[dict]:
    """Return contiguous coverage of the whole day (0..1440 min), Off Duty in gaps."""
    midnight = _midnight(day, tzinfo)
    segments = sorted(segments, key=lambda s: s.start)
    coverage: list[dict] = []
    cursor_min = 0

    def add(duty, start_min, end_min, *, event_type=None, is_event_start=False, label=""):
        coverage.append(
            {
                "duty_status": duty.value if isinstance(duty, DutyStatus) else duty,
                "start_minute": start_min,
                "end_minute": end_min,
                "event_type": event_type.value if event_type else None,
                "is_event_start": is_event_start,
                "label": label,
            }
        )

    for seg in segments:
        s_min = _minutes(seg.start - midnight)
        e_min = _minutes(seg.end - midnight)
        s_min = max(0, min(MINUTES_PER_DAY, s_min))
        e_min = max(0, min(MINUTES_PER_DAY, e_min))
        if e_min <= s_min:
            continue
        if s_min > cursor_min:
            add(DutyStatus.OFF_DUTY, cursor_min, s_min)
        add(
            seg.duty,
            s_min,
            e_min,
            event_type=seg.event_type,
            is_event_start=seg.is_event_start,
            label=seg.label,
        )
        cursor_min = e_min

    if cursor_min < MINUTES_PER_DAY:
        add(DutyStatus.OFF_DUTY, cursor_min, MINUTES_PER_DAY)
    return coverage


def _format_time(minute_of_day: int) -> str:
    hours, minutes = divmod(minute_of_day, 60)
    return f"{hours:02d}:{minutes:02d}"


def _cycle_snapshots(
    events: list[TimelineEvent], initial_cycle_minutes: int
) -> list[tuple[datetime, int]]:
    """Modeled cycle-used minutes right after each event ends (restart -> 0)."""
    running = initial_cycle_minutes
    snapshots: list[tuple[datetime, int]] = []
    for event in events:
        _, end = _parse(event)
        if event.type is EventType.CYCLE_RESTART:
            running = 0
        elif event.type in _ON_DUTY_TYPES:
            running += event.duration_minutes
        snapshots.append((end, running))
    return snapshots


def build_daily_logs(
    events: list[TimelineEvent],
    *,
    initial_cycle_used_minutes: int = 0,
    metadata: dict | None = None,
) -> list[dict]:
    """Build the ordered list of per-day log dictionaries for the response."""
    if not events:
        return []

    meta = {**DEFAULT_METADATA, **(metadata or {})}
    tzinfo = datetime.fromisoformat(events[0].start_at).tzinfo
    buckets = _split_by_day(events)
    snapshots = _cycle_snapshots(events, initial_cycle_used_minutes)

    first_day = min(buckets)
    last_day = max(buckets)

    logs: list[dict] = []
    for day in _date_range(first_day, last_day):
        day_segments = buckets.get(day, [])
        coverage = _fill_day(day, day_segments, tzinfo)

        totals = {s.value: 0 for s in DutyStatus}
        for part in coverage:
            totals[part["duty_status"]] += part["end_minute"] - part["start_minute"]

        total_miles = round(sum(seg.miles for seg in day_segments), 2)

        remarks = [
            {
                "time": _format_time(part["start_minute"]),
                "location": part["label"] or "En route",
                "activity": _ACTIVITY_BY_TYPE.get(
                    EventType(part["event_type"]) if part["event_type"] else None,
                    "Status change",
                ),
            }
            for part in coverage
            if part["is_event_start"] and part["event_type"]
        ]

        # From/to labels: first and last located segment of the day.
        located = [p for p in coverage if p["label"]]
        from_label = located[0]["label"] if located else ""
        to_label = located[-1]["label"] if located else ""

        day_end = _midnight(day + timedelta(days=1), tzinfo)
        cycle_end = initial_cycle_used_minutes
        for end_dt, value in snapshots:
            if end_dt <= day_end:
                cycle_end = value
            else:
                break
        on_duty_today = totals[DutyStatus.DRIVING.value] + totals[
            DutyStatus.ON_DUTY_NOT_DRIVING.value
        ]

        assert (
            sum(totals.values()) == MINUTES_PER_DAY
        ), "daily log must total exactly 1,440 minutes"

        logs.append(
            {
                "date": day.isoformat(),
                "from_label": from_label,
                "to_label": to_label,
                "total_miles": total_miles,
                "segments": coverage,
                "totals": totals,
                "remarks": remarks,
                "recap": {
                    "on_duty_minutes_today": on_duty_today,
                    "cycle_used_minutes_end_of_day": cycle_end,
                    "cycle_hours_available": round(max(0, 4200 - cycle_end) / 60.0, 2),
                },
                "metadata": meta,
            }
        )

    return logs
