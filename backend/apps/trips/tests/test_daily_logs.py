"""
Tests for the daily-log builder.

Verifies the core invariants: every day totals exactly 1,440 minutes with no
gaps or overlaps, cross-midnight events split correctly, per-day driving miles
are prorated, and remarks are generated at real status changes.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from apps.trips.services.daily_log_builder import (
    MINUTES_PER_DAY,
    build_daily_logs,
)
from apps.trips.services.hos_scheduler import plan_trip
from apps.trips.types import DrivingLeg, DutyStatus, EventType, TimelineEvent

CST = timezone(timedelta(hours=-5))
START = datetime(2026, 7, 20, 8, 0, tzinfo=CST)


def leg(minutes: int, end: EventType | None = None, mph: float = 60.0) -> DrivingLeg:
    return DrivingLeg(minutes * (mph / 60.0), minutes, end_event=end)


def _logs_for(legs, cycle_hours: float = 0.0):
    schedule = plan_trip(legs, START, cycle_hours)
    return build_daily_logs(
        schedule.events, initial_cycle_used_minutes=round(cycle_hours * 60)
    )


def _assert_day_valid(log: dict) -> None:
    # Exactly 1,440 minutes across the four statuses.
    assert sum(log["totals"].values()) == MINUTES_PER_DAY
    # Contiguous coverage 0..1440 with no gaps/overlaps.
    segments = log["segments"]
    assert segments[0]["start_minute"] == 0
    assert segments[-1]["end_minute"] == MINUTES_PER_DAY
    for prev, cur in zip(segments, segments[1:]):
        assert prev["end_minute"] == cur["start_minute"]
    for seg in segments:
        assert seg["end_minute"] > seg["start_minute"]
        assert seg["duty_status"] in {s.value for s in DutyStatus}


def test_single_day_totals_1440():
    logs = _logs_for([leg(300, EventType.PICKUP), leg(180, EventType.DROPOFF)])
    assert len(logs) == 1
    _assert_day_valid(logs[0])


def test_first_day_starts_off_duty_until_departure():
    # Trip starts 08:00; midnight..08:00 (480 min) must be Off Duty.
    logs = _logs_for([leg(120, EventType.DROPOFF)])
    first = logs[0]["segments"][0]
    assert first["duty_status"] == DutyStatus.OFF_DUTY.value
    assert first["start_minute"] == 0
    assert first["end_minute"] == 480  # 08:00


def test_multiday_trip_all_days_total_1440():
    logs = _logs_for(
        [leg(370, EventType.PICKUP), leg(2400, EventType.DROPOFF)], cycle_hours=10.0
    )
    assert len(logs) >= 3
    for log in logs:
        _assert_day_valid(log)


def test_cross_midnight_event_is_split():
    # A 10-hour sleeper starting late crosses midnight; both days must be valid
    # and the sleeper minutes must appear on both calendar days.
    logs = _logs_for([leg(720, EventType.DROPOFF)])  # forces an overnight sleeper
    assert len(logs) >= 2
    for log in logs:
        _assert_day_valid(log)
    # Sleeper time appears on more than one day (split across midnight).
    days_with_sleeper = [
        log for log in logs if log["totals"][DutyStatus.SLEEPER_BERTH.value] > 0
    ]
    assert len(days_with_sleeper) >= 2


def test_driving_miles_prorated_and_conserved():
    legs = [leg(600, EventType.PICKUP), leg(1200, EventType.DROPOFF)]
    schedule = plan_trip(legs, START, 0.0)
    logs = build_daily_logs(schedule.events)
    total_miles = sum(log["total_miles"] for log in logs)
    assert abs(total_miles - (600 + 1200)) < 1.0


def test_remarks_reference_real_events():
    logs = _logs_for([leg(120, EventType.PICKUP), leg(120, EventType.DROPOFF)])
    activities = [r["activity"] for log in logs for r in log["remarks"]]
    assert "Pickup" in activities
    assert "Drop-off" in activities
    assert "Began driving" in activities
    for log in logs:
        for r in log["remarks"]:
            assert ":" in r["time"]  # HH:MM
            assert r["location"]


def test_recap_present_and_bounded():
    logs = _logs_for([leg(300, EventType.PICKUP), leg(180, EventType.DROPOFF)], 20.0)
    recap = logs[0]["recap"]
    assert 0 <= recap["cycle_hours_available"] <= 70
    assert recap["on_duty_minutes_today"] >= 0


def test_metadata_flagged_demo():
    logs = _logs_for([leg(60, EventType.DROPOFF)])
    meta = logs[0]["metadata"]
    assert meta["is_demo"] is True
    assert meta["driver_name"] == "Assessment Driver"


def test_empty_events_returns_no_logs():
    assert build_daily_logs([]) == []


def test_manual_midnight_split_totals():
    # Hand-built event crossing midnight: 22:00 -> 02:00 driving (240 min).
    start = datetime(2026, 7, 20, 22, 0, tzinfo=CST)
    end = datetime(2026, 7, 21, 2, 0, tzinfo=CST)
    event = TimelineEvent(
        type=EventType.DRIVING,
        duty_status=DutyStatus.DRIVING,
        start_at=start.isoformat(),
        end_at=end.isoformat(),
        duration_minutes=240,
        distance_miles=240.0,
        location_label="Somewhere",
        meta={"start_distance_miles": 0.0, "end_distance_miles": 240.0},
    )
    logs = build_daily_logs([event])
    assert len(logs) == 2
    # Day 1: 22:00..24:00 = 120 driving min; Day 2: 00:00..02:00 = 120 min.
    assert logs[0]["totals"][DutyStatus.DRIVING.value] == 120
    assert logs[1]["totals"][DutyStatus.DRIVING.value] == 120
    # Miles prorated 120/120.
    assert abs(logs[0]["total_miles"] - 120.0) < 0.01
    assert abs(logs[1]["total_miles"] - 120.0) < 0.01
    for log in logs:
        _assert_day_valid(log)
