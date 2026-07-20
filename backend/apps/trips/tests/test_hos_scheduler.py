"""
Unit tests for the pure HOS scheduling engine.

Covers every "Minimum automated case" in docs/HOS_RULES.md plus interaction
cases, using synthetic in-memory driving legs (no network, no DB). A shared
invariant checker re-derives the HOS clocks from the emitted timeline and
asserts no rule is ever violated.

Convention: legs use 60 mph (mi_per_min == 1), so a leg's distance in miles
equals its duration in minutes, which keeps expected values easy to read.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from apps.trips.services import hos_scheduler as hs
from apps.trips.services.hos_scheduler import ScheduleResult, _Planner, plan_trip
from apps.trips.types import DrivingLeg, DutyStatus, EventType

CST = timezone(timedelta(hours=-5))
START = datetime(2026, 7, 20, 8, 0, tzinfo=CST)


def leg(minutes: int, end: EventType | None = None, mph: float = 60.0) -> DrivingLeg:
    miles = minutes * (mph / 60.0)
    return DrivingLeg(distance_miles=miles, duration_minutes=minutes, end_event=end)


def run(legs, cycle_hours: float = 0.0, start: datetime = START) -> ScheduleResult:
    return plan_trip(legs, start, cycle_hours)


# --------------------------------------------------------------------------- #
# Invariant checker
# --------------------------------------------------------------------------- #


def assert_hos_valid(result: ScheduleResult, initial_cycle_hours: float = 0.0) -> None:
    events = result.events
    assert events, "expected at least one event"

    # Contiguous, ordered, minute-precise, positive-duration.
    for prev, cur in zip(events, events[1:]):
        assert prev.end_at == cur.start_at, "events must be contiguous"
    for e in events:
        s = datetime.fromisoformat(e.start_at)
        en = datetime.fromisoformat(e.end_at)
        assert e.duration_minutes > 0
        assert en - s == timedelta(minutes=e.duration_minutes)
        assert e.distance_miles >= 0

    # Re-derive clocks and assert limits are never exceeded.
    drive_since_reset = 0
    drive_since_break = 0
    cycle = round(initial_cycle_hours * 60)
    window_start: datetime | None = None

    for e in events:
        s = datetime.fromisoformat(e.start_at)
        en = datetime.fromisoformat(e.end_at)
        dur = e.duration_minutes

        if e.type is EventType.DRIVING:
            if window_start is None:
                window_start = s
            assert drive_since_reset + dur <= hs.ELEVEN_HOUR, "11-hour limit exceeded"
            assert drive_since_break + dur <= hs.EIGHT_HOUR, "8-hour break exceeded"
            assert cycle + dur <= hs.SEVENTY_HOUR, "70-hour cycle exceeded"
            elapsed = int((en - window_start).total_seconds() // 60)
            assert elapsed <= hs.FOURTEEN_HOUR, "14-hour window exceeded"
            drive_since_reset += dur
            drive_since_break += dur
            cycle += dur
        elif e.type in (EventType.PICKUP, EventType.DROPOFF, EventType.FUEL):
            if window_start is None:
                window_start = s
            cycle += dur
            drive_since_break = 0  # qualifies as a 30-min break
        elif e.type is EventType.REST_BREAK:
            drive_since_break = 0
        elif e.type is EventType.SLEEPER_BERTH:
            drive_since_reset = 0
            drive_since_break = 0
            window_start = None
        elif e.type is EventType.CYCLE_RESTART:
            cycle = 0
            drive_since_reset = 0
            drive_since_break = 0
            window_start = None
    # Note: the cycle total may legitimately exceed 70h via On-Duty work; the
    # real invariant (no DRIVING past 70h) is checked per driving event above.


def driving_minutes(result: ScheduleResult) -> int:
    return sum(e.duration_minutes for e in result.events if e.type is EventType.DRIVING)


def driving_miles(result: ScheduleResult) -> float:
    return sum(
        e.distance_miles for e in result.events if e.type is EventType.DRIVING
    )


# --------------------------------------------------------------------------- #
# Case 1: under 8 driving hours -> no required break
# --------------------------------------------------------------------------- #


def test_short_trip_has_no_rest_break():
    result = run([leg(420)])  # 7 hours
    assert result.rest_break_count == 0
    assert result.overnight_rest_count == 0
    assert result.cycle_restart_count == 0
    assert driving_minutes(result) == 420
    assert_hos_valid(result)


# --------------------------------------------------------------------------- #
# Case 2: nine driving hours -> exactly one 30-minute break
# --------------------------------------------------------------------------- #


def test_nine_hour_trip_inserts_one_break():
    result = run([leg(540)])  # 9 hours
    assert result.rest_break_count == 1
    assert result.overnight_rest_count == 0
    breaks = [e for e in result.events if e.type is EventType.REST_BREAK]
    assert breaks[0].duration_minutes == 30
    assert breaks[0].duty_status is DutyStatus.OFF_DUTY
    # The break lands at 8 cumulative driving hours (480 min after 08:00).
    assert breaks[0].start_at == (START + timedelta(minutes=480)).isoformat()
    assert driving_minutes(result) == 540
    assert_hos_valid(result)


# --------------------------------------------------------------------------- #
# Case 3: over 11 driving hours -> a 10-hour reset, no daily driving > 11h
# --------------------------------------------------------------------------- #


def test_over_eleven_hours_inserts_sleeper_and_caps_driving():
    result = run([leg(720)])  # 12 hours of driving
    assert result.overnight_rest_count == 1
    assert result.rest_break_count == 1  # break at 8h still required
    sleepers = [e for e in result.events if e.type is EventType.SLEEPER_BERTH]
    assert sleepers[0].duration_minutes == 600
    assert sleepers[0].reason_code == hs.REASON_ELEVEN_HOUR

    # No contiguous driving run exceeds 11 hours between resets.
    run_total = 0
    for e in result.events:
        if e.type is EventType.DRIVING:
            run_total += e.duration_minutes
            assert run_total <= hs.ELEVEN_HOUR
        elif e.type in (EventType.SLEEPER_BERTH, EventType.CYCLE_RESTART):
            run_total = 0
    assert driving_minutes(result) == 720
    assert_hos_valid(result)


# --------------------------------------------------------------------------- #
# Case 4: 14-hour window -> no driving after the window expires
# --------------------------------------------------------------------------- #


def test_driving_stops_at_fourteen_hour_window():
    # White-box: open a window 13.5 hours ago so only 30 driving minutes remain
    # before the 14-hour boundary, then drive a leg that needs more.
    planner = _Planner(START, cycle_used_minutes=0)
    planner.window_start = START - timedelta(minutes=810)
    planner.drive_leg(leg(120))  # wants 2 hours of driving

    types = [e.type for e in planner.events]
    assert types[0] is EventType.DRIVING
    assert planner.events[0].duration_minutes == 30  # capped at window boundary
    assert types[1] is EventType.SLEEPER_BERTH
    assert planner.events[1].reason_code == hs.REASON_FOURTEEN_HOUR
    # Remaining 90 minutes drive in the fresh window.
    assert planner.events[2].type is EventType.DRIVING
    assert planner.events[2].duration_minutes == 90


# --------------------------------------------------------------------------- #
# Case 5: fueling before 1,000 miles, On Duty, resets the break counter
# --------------------------------------------------------------------------- #


def test_fuel_event_before_1000_miles():
    result = run([leg(1000)])  # 1,000 miles at 60 mph
    fuels = [e for e in result.events if e.type is EventType.FUEL]
    assert len(fuels) >= 1
    first_fuel = fuels[0]
    assert first_fuel.duty_status is DutyStatus.ON_DUTY_NOT_DRIVING
    assert first_fuel.duration_minutes == 30
    assert first_fuel.reason_code == hs.REASON_FUEL
    # Placed before the route passes 1,000 miles (target 900).
    assert first_fuel.meta["start_distance_miles"] < 1000.0
    assert first_fuel.meta["start_distance_miles"] >= 850.0
    assert_hos_valid(result)


def test_fuel_resets_break_and_counts_toward_cycle():
    planner = _Planner(START, cycle_used_minutes=0)
    planner.drive_since_break = 200
    planner.cycle_used = 100
    planner._fuel()
    assert planner.drive_since_break == 0
    assert planner.dist_since_fuel == 0.0
    assert planner.cycle_used == 130  # +30 On Duty minutes


# --------------------------------------------------------------------------- #
# Case 6: cycle exhaustion -> stop at 70h and insert a 34-hour restart
# --------------------------------------------------------------------------- #


def test_cycle_exhaustion_inserts_restart():
    # 69 hours already used -> only 60 modeled cycle minutes remain.
    result = run([leg(600, EventType.DROPOFF)], cycle_hours=69.0)
    assert result.cycle_restart_count == 1
    restart = next(e for e in result.events if e.type is EventType.CYCLE_RESTART)
    assert restart.duration_minutes == hs.THIRTY_FOUR_HOUR
    assert restart.duty_status is DutyStatus.OFF_DUTY
    assert restart.reason_code == hs.REASON_CYCLE

    # Driving stops exactly at the 70-hour boundary: first driving run is 60 min.
    first_driving = next(e for e in result.events if e.type is EventType.DRIVING)
    assert first_driving.duration_minutes == 60
    assert_hos_valid(result, initial_cycle_hours=69.0)


def test_zero_available_cycle_restarts_before_any_driving():
    result = run([leg(120, EventType.DROPOFF)], cycle_hours=70.0)
    # With no cycle available, a restart must precede the first driving.
    first_significant = next(
        e for e in result.events if e.type in (EventType.DRIVING, EventType.CYCLE_RESTART)
    )
    assert first_significant.type is EventType.CYCLE_RESTART
    assert result.cycle_restart_count == 1
    assert_hos_valid(result, initial_cycle_hours=70.0)


# --------------------------------------------------------------------------- #
# Case 7: pickup and drop-off are exactly 60 minutes, On Duty
# --------------------------------------------------------------------------- #


def test_pickup_and_dropoff_are_sixty_minutes_on_duty():
    result = run([leg(120, EventType.PICKUP), leg(120, EventType.DROPOFF)])
    pickups = [e for e in result.events if e.type is EventType.PICKUP]
    dropoffs = [e for e in result.events if e.type is EventType.DROPOFF]
    assert len(pickups) == 1 and len(dropoffs) == 1
    for e in pickups + dropoffs:
        assert e.duration_minutes == 60
        assert e.duty_status is DutyStatus.ON_DUTY_NOT_DRIVING
    # Drop-off is the final event and completes the trip.
    assert result.events[-1].type is EventType.DROPOFF
    assert_hos_valid(result)


def test_pickup_qualifies_as_break():
    # Drive 8 hours, then pickup: the pickup should satisfy the break so no
    # separate REST_BREAK is inserted for that 8-hour boundary.
    result = run([leg(480, EventType.PICKUP), leg(120, EventType.DROPOFF)])
    # The 480-min boundary coincides with arrival at pickup; pickup (>=30 min
    # On Duty) resets the break counter.
    assert result.rest_break_count == 0
    assert_hos_valid(result)


# --------------------------------------------------------------------------- #
# Case 10: scheduled driving distance reconciles to route distance
# --------------------------------------------------------------------------- #


def test_driving_distance_reconciles_to_total():
    result = run([leg(1200, EventType.PICKUP), leg(900, EventType.DROPOFF)])
    expected = 1200 + 900  # miles at 60 mph
    assert abs(result.total_distance_miles - expected) < 0.01
    assert abs(driving_miles(result) - expected) < 0.01


# --------------------------------------------------------------------------- #
# General properties
# --------------------------------------------------------------------------- #


def test_summary_fields_are_consistent():
    result = run([leg(300, EventType.PICKUP), leg(300, EventType.DROPOFF)])
    assert result.raw_driving_minutes == 600
    assert result.departure_at == result.events[0].start_at
    assert result.arrival_at == result.events[-1].end_at
    # Compliant duration is at least the raw driving time (adds stops).
    assert result.compliant_trip_minutes >= result.raw_driving_minutes


def test_scheduler_is_deterministic():
    legs = [leg(700, EventType.PICKUP), leg(1300, EventType.DROPOFF)]
    a = run(legs, cycle_hours=10.0)
    b = run(legs, cycle_hours=10.0)
    assert [(e.type, e.start_at, e.duration_minutes) for e in a.events] == [
        (e.type, e.start_at, e.duration_minutes) for e in b.events
    ]


def test_long_multiday_trip_is_valid():
    # NY -> Pittsburgh -> LA style: long, multi-constraint.
    result = run(
        [leg(370, EventType.PICKUP), leg(2400, EventType.DROPOFF)],
        cycle_hours=10.0,
    )
    assert result.overnight_rest_count >= 2
    assert result.fuel_stop_count >= 2
    assert result.rest_break_count >= 1
    assert_hos_valid(result, initial_cycle_hours=10.0)


def test_all_durations_are_integer_minutes():
    result = run([leg(1000, EventType.PICKUP), leg(1000, EventType.DROPOFF)], 5.0)
    for e in result.events:
        assert isinstance(e.duration_minutes, int)
        assert e.duration_minutes > 0


def test_trip_start_must_be_timezone_aware():
    naive = datetime(2026, 7, 20, 8, 0)
    with pytest.raises(ValueError, match="timezone-aware"):
        plan_trip([leg(60)], naive, 0.0)
