"""
Pure, deterministic Hours-of-Service scheduling engine.

Given a list of ``DrivingLeg``s, a fixed timezone-aware trip start, and the
driver's current cycle usage, this emits an ordered, contiguous list of
``TimelineEvent``s that respects the FMCSA property-carrying rules modeled by
this assessment (see ``docs/HOS_RULES.md``).

Design constraints (ADR-003):
- No HTTP, ORM, filesystem, or real wall-clock dependency. The only time input
  is ``trip_start``; everything else is arithmetic on integer minutes.
- Deterministic: identical inputs always produce identical output.
- Route-progress interpolation and reverse-geocode labeling are NOT done here
  (Phase 4); events carry cumulative route distance in ``meta`` so a later
  stage can map them to coordinates.

All internal durations are integer minutes. Distances are miles (float), and
each driving chunk is assigned miles proportional to the leg's average speed so
the scheduled distance reconciles exactly to the leg distances.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from apps.trips.types import (
    DrivingLeg,
    DutyStatus,
    EventType,
    TimelineEvent,
)

# --- HOS limits, in minutes -------------------------------------------------

ELEVEN_HOUR = 11 * 60  # 660 driving minutes per qualifying reset
FOURTEEN_HOUR = 14 * 60  # 840 elapsed-minute driving window
EIGHT_HOUR = 8 * 60  # 480 cumulative driving minutes before a 30-min break
SEVENTY_HOUR = 70 * 60  # 4200 modeled cycle minutes (conservative bucket)
TEN_HOUR_RESET = 10 * 60  # 600-minute sleeper reset
THIRTY_FOUR_HOUR = 34 * 60  # 2040-minute off-duty cycle restart
BREAK_MINUTES = 30
PICKUP_MINUTES = 60
DROPOFF_MINUTES = 60
FUEL_MINUTES = 30

FUEL_INTERVAL_MILES = 900.0  # plan fuel every ~900 mi (stays under 1,000)

# --- Machine-readable reason codes for scheduler-created stops --------------

REASON_ELEVEN_HOUR = "ELEVEN_HOUR_LIMIT"
REASON_FOURTEEN_HOUR = "FOURTEEN_HOUR_WINDOW"
REASON_EIGHT_HOUR_BREAK = "EIGHT_HOUR_BREAK"
REASON_FUEL = "FUEL_INTERVAL"
REASON_CYCLE = "CYCLE_EXHAUSTED"
REASON_PICKUP = "PICKUP"
REASON_DROPOFF = "DROPOFF"


@dataclass
class ScheduleResult:
    """The scheduler's output: the timeline plus derived summary numbers."""

    events: list[TimelineEvent]
    total_distance_miles: float
    raw_driving_minutes: int
    compliant_trip_minutes: int
    departure_at: str
    arrival_at: str
    fuel_stop_count: int
    rest_break_count: int
    overnight_rest_count: int
    cycle_restart_count: int


class _Planner:
    """Mutable scheduling state machine. One instance per ``plan_trip`` call."""

    def __init__(self, trip_start: datetime, cycle_used_minutes: int) -> None:
        if trip_start.tzinfo is None:
            raise ValueError("trip_start must be timezone-aware")
        self.now = trip_start
        self.cycle_used = cycle_used_minutes
        self.drive_since_reset = 0  # for the 11-hour limit
        self.drive_since_break = 0  # for the 8-hour / 30-min break rule
        self.window_start: datetime | None = None  # 14-hour window anchor
        self.dist_since_fuel = 0.0
        self.cum_miles = 0.0
        self.events: list[TimelineEvent] = []
        # Pending contiguous-driving buffer so we emit one DRIVING event per
        # uninterrupted stretch instead of many adjacent fragments.
        self._p_start: datetime | None = None
        self._p_minutes = 0
        self._p_miles = 0.0
        self._p_cum_start = 0.0

    # -- window helpers ------------------------------------------------------

    def window_remaining(self) -> int:
        if self.window_start is None:
            return FOURTEEN_HOUR
        elapsed = int((self.now - self.window_start).total_seconds() // 60)
        return FOURTEEN_HOUR - elapsed

    # -- event emission ------------------------------------------------------

    def _append(
        self,
        event_type: EventType,
        duty: DutyStatus,
        start: datetime,
        minutes: int,
        *,
        miles: float = 0.0,
        description: str = "",
        reason_code: str = "",
        cum_start: float | None = None,
        cum_end: float | None = None,
    ) -> datetime:
        end = start + timedelta(minutes=minutes)
        cs = self.cum_miles if cum_start is None else cum_start
        ce = self.cum_miles if cum_end is None else cum_end
        self.events.append(
            TimelineEvent(
                type=event_type,
                duty_status=duty,
                start_at=start.isoformat(),
                end_at=end.isoformat(),
                duration_minutes=minutes,
                distance_miles=round(miles, 4),
                description=description,
                reason_code=reason_code,
                meta={
                    "start_distance_miles": round(cs, 4),
                    "end_distance_miles": round(ce, 4),
                },
            )
        )
        return end

    def _flush_driving(self) -> None:
        if self._p_minutes <= 0 or self._p_start is None:
            return
        self._append(
            EventType.DRIVING,
            DutyStatus.DRIVING,
            self._p_start,
            self._p_minutes,
            miles=self._p_miles,
            description="Driving",
            cum_start=self._p_cum_start,
            cum_end=self.cum_miles,
        )
        self._p_start = None
        self._p_minutes = 0
        self._p_miles = 0.0

    # -- non-driving events --------------------------------------------------

    def _sleeper_reset(self, reason: str, description: str) -> None:
        start = self.now
        self.now = self._append(
            EventType.SLEEPER_BERTH,
            DutyStatus.SLEEPER_BERTH,
            start,
            TEN_HOUR_RESET,
            description=description,
            reason_code=reason,
        )
        # 10 consecutive hours off resets the daily driving clocks and window,
        # but NOT the modeled 70-hour cycle.
        self.drive_since_reset = 0
        self.drive_since_break = 0
        self.window_start = None

    def _cycle_restart(self) -> None:
        start = self.now
        self.now = self._append(
            EventType.CYCLE_RESTART,
            DutyStatus.OFF_DUTY,
            start,
            THIRTY_FOUR_HOUR,
            description="34-hour restart (modeled 70-hour cycle exhausted)",
            reason_code=REASON_CYCLE,
        )
        self.cycle_used = 0
        self.drive_since_reset = 0
        self.drive_since_break = 0
        self.window_start = None

    def _rest_break(self) -> None:
        start = self.now
        self.now = self._append(
            EventType.REST_BREAK,
            DutyStatus.OFF_DUTY,
            start,
            BREAK_MINUTES,
            description="30-minute rest break",
            reason_code=REASON_EIGHT_HOUR_BREAK,
        )
        # A 30-min break resets driving-since-break only. It does NOT reset the
        # 11-hour clock and does NOT pause/extend the 14-hour window.
        self.drive_since_break = 0

    def _fuel(self) -> None:
        start = self.now
        if self.window_start is None:
            self.window_start = start
        self.now = self._append(
            EventType.FUEL,
            DutyStatus.ON_DUTY_NOT_DRIVING,
            start,
            FUEL_MINUTES,
            description="Planned fuel stop along route",
            reason_code=REASON_FUEL,
        )
        # Fuel is On Duty (counts toward cycle) and qualifies as the 30-min
        # break (resets driving-since-break). It does not reset the 11-hour
        # clock or the 14-hour window.
        self.cycle_used += FUEL_MINUTES
        self.drive_since_break = 0
        self.dist_since_fuel = 0.0

    def _operational(
        self, event_type: EventType, minutes: int, description: str, reason: str
    ) -> None:
        self._flush_driving()
        start = self.now
        if self.window_start is None:
            self.window_start = start
        self.now = self._append(
            event_type,
            DutyStatus.ON_DUTY_NOT_DRIVING,
            start,
            minutes,
            description=description,
            reason_code=reason,
        )
        # Pickup/drop-off are On Duty (count toward cycle) and, being >= 30
        # consecutive non-driving minutes, satisfy the break requirement.
        self.cycle_used += minutes
        self.drive_since_break = 0

    # -- constraint servicing ------------------------------------------------

    def _service_if_blocked(self) -> bool:
        """If a limit currently blocks driving, insert its event and return True.

        Priority (most disruptive first): cycle exhaustion, 11-hour limit,
        14-hour window, then the fuel interval, then the standalone 8-hour
        break. Fuel is checked before the break on purpose: a 30-minute fuel
        stop already satisfies the break requirement, so when both come due at
        once we emit a single fuel stop instead of a break immediately followed
        by fuel.
        """
        if self.cycle_used >= SEVENTY_HOUR:
            self._flush_driving()
            self._cycle_restart()
            return True
        if self.drive_since_reset >= ELEVEN_HOUR:
            self._flush_driving()
            self._sleeper_reset(
                REASON_ELEVEN_HOUR,
                "10-hour sleeper berth (reached 11-hour driving limit)",
            )
            return True
        if self.window_start is not None and self.window_remaining() <= 0:
            self._flush_driving()
            self._sleeper_reset(
                REASON_FOURTEEN_HOUR,
                "10-hour sleeper berth (14-hour driving window elapsed)",
            )
            return True
        if self.dist_since_fuel >= FUEL_INTERVAL_MILES:
            self._flush_driving()
            self._fuel()
            return True
        if self.drive_since_break >= EIGHT_HOUR:
            self._flush_driving()
            self._rest_break()
            return True
        return False

    # -- driving -------------------------------------------------------------

    def drive_leg(self, leg: DrivingLeg) -> None:
        remaining = int(leg.duration_minutes)
        if remaining <= 0:
            return
        mi_per_min = leg.distance_miles / leg.duration_minutes

        while remaining > 0:
            if self._service_if_blocked():
                continue

            # The first driving (or on-duty) minute after a reset opens a new
            # 14-hour window.
            if self.window_start is None:
                self.window_start = self.now

            # Largest chunk we may drive before the next constraint boundary.
            chunk = min(
                ELEVEN_HOUR - self.drive_since_reset,
                EIGHT_HOUR - self.drive_since_break,
                SEVENTY_HOUR - self.cycle_used,
                self.window_remaining(),
                remaining,
            )
            if mi_per_min > 0:
                fuel_minutes = (FUEL_INTERVAL_MILES - self.dist_since_fuel) / mi_per_min
                chunk = min(chunk, max(1, round(fuel_minutes)))
            chunk = int(chunk)
            if chunk <= 0:
                chunk = 1  # guarantee forward progress

            if self._p_minutes == 0:
                self._p_start = self.now
                self._p_cum_start = self.cum_miles

            miles = chunk * mi_per_min
            self.now += timedelta(minutes=chunk)
            remaining -= chunk
            self.drive_since_reset += chunk
            self.drive_since_break += chunk
            self.cycle_used += chunk
            self.dist_since_fuel += miles
            self.cum_miles += miles
            self._p_minutes += chunk
            self._p_miles += miles

        self._flush_driving()


def plan_trip(
    legs: list[DrivingLeg],
    trip_start: datetime,
    current_cycle_used_hours: float,
) -> ScheduleResult:
    """Build the compliant HOS timeline for the given driving legs.

    Args:
        legs: ordered driving legs; each leg is driven (with HOS stops
            inserted) and then its ``end_event`` (pickup/drop-off) is emitted.
        trip_start: timezone-aware start of the trip (also the log time base).
        current_cycle_used_hours: 0..70; converted to minutes with rounding and
            treated as already-consumed modeled cycle time.

    Returns:
        A ``ScheduleResult`` with the ordered timeline and summary counts.
    """
    cycle_used_minutes = round(current_cycle_used_hours * 60)
    planner = _Planner(trip_start, cycle_used_minutes)

    for leg in legs:
        planner.drive_leg(leg)
        if leg.end_event is EventType.PICKUP:
            planner._operational(
                EventType.PICKUP, PICKUP_MINUTES, "Pickup", REASON_PICKUP
            )
        elif leg.end_event is EventType.DROPOFF:
            planner._operational(
                EventType.DROPOFF, DROPOFF_MINUTES, "Drop-off", REASON_DROPOFF
            )

    events = planner.events
    total_distance = sum(leg.distance_miles for leg in legs)
    raw_driving = sum(int(leg.duration_minutes) for leg in legs)

    departure_at = events[0].start_at if events else trip_start.isoformat()
    arrival_at = events[-1].end_at if events else trip_start.isoformat()
    if events:
        start_dt = datetime.fromisoformat(events[0].start_at)
        end_dt = datetime.fromisoformat(events[-1].end_at)
        compliant_minutes = int((end_dt - start_dt).total_seconds() // 60)
    else:
        compliant_minutes = 0

    def _count(event_type: EventType) -> int:
        return sum(1 for e in events if e.type is event_type)

    return ScheduleResult(
        events=events,
        total_distance_miles=round(total_distance, 4),
        raw_driving_minutes=raw_driving,
        compliant_trip_minutes=compliant_minutes,
        departure_at=departure_at,
        arrival_at=arrival_at,
        fuel_stop_count=_count(EventType.FUEL),
        rest_break_count=_count(EventType.REST_BREAK),
        overnight_rest_count=_count(EventType.SLEEPER_BERTH),
        cycle_restart_count=_count(EventType.CYCLE_RESTART),
    )
