# HOS Requirements Summary

## Status and source

This document is the implementation contract for the assessment’s Hours of Service model. It summarizes:

- `docs/MASTER_IMPLEMENTATION_SPEC.md`
- The April 2022 FMCSA *Interstate Truck Driver’s Guide to Hours of Service for Property Carriers*, especially pages 5–11 and 15–19

The FMCSA guide states that it is guidance and not a substitute for the regulations. This application is an assessment/demo planner, not a certified ELD or legal-compliance product.

## Operating assumptions

Model one property-carrying CMV driver in interstate commerce on a 70-hour/8-day schedule.

Included assumptions:

- The driver begins after at least 10 consecutive hours of qualifying rest.
- The route is current location → pickup → drop-off.
- Pickup and drop-off each take exactly 60 minutes.
- The truck begins with sufficient fuel.
- Fuel is planned every 900 route miles so the plan does not exceed 1,000 miles between fuel events.
- Each fuel event lasts exactly 30 minutes.
- Pickup, drop-off, and fuel are On Duty, Not Driving.
- Overnight daily resets use 10 consecutive hours in Sleeper Berth.
- Modeled cycle restarts use 34 consecutive hours Off Duty.
- The optional `trip_start` makes results reproducible; otherwise planning begins at the current timezone-aware date/time.
- Every schedule and log uses the trip-start timezone, even if the route crosses timezones.

Excluded behavior:

- Adverse-driving-condition exception
- Short-haul exceptions
- Personal conveyance
- Split-sleeper calculations
- Team-driver calculations
- Exact rolling recapture from prior days
- Real truck-stop POI selection

## Duty statuses

| Status | Counts toward 70-hour cycle | Qualifies as non-driving break | Use in this assessment |
| --- | ---: | ---: | --- |
| Off Duty | No | Yes, when consecutive for at least 30 minutes | Normal break, unallocated daily time, 34-hour restart |
| Sleeper Berth | No | Yes, when consecutive for at least 30 minutes | Ten-hour overnight reset |
| Driving | Yes | No | Route travel |
| On Duty, Not Driving | Yes | Yes, when consecutive for at least 30 minutes | Pickup, drop-off, fueling |

A qualifying 30-minute break may consist of consecutive non-driving statuses. The initial implementation can emit a single event/status per planned break, while remaining compatible with consecutive mixed-status validation.

## Rule 1: 11-hour driving limit

After at least 10 consecutive hours of qualifying rest, the driver may accumulate no more than 11 hours (660 minutes) of Driving.

Implementation requirements:

- Count only Driving toward the 11-hour total.
- Pickup, drop-off, fuel, and normal breaks do not add driving time.
- Once 660 minutes are reached, add a 10-hour Sleeper Berth event before any more driving.
- Reset the driving total only after a qualifying 10-hour reset or 34-hour restart.

Required invariant: no driving segment may make the accumulated driving since reset exceed 660 minutes.

## Rule 2: 14-hour driving window

The 14-hour window is 14 consecutive elapsed hours beginning when the first Driving or On Duty, Not Driving event starts after a qualifying reset.

Implementation requirements:

- The window runs on wall-clock time.
- Pickup, drop-off, fuel, Off Duty breaks, and Sleeper Berth time inside an active window do not pause or extend it.
- Driving must end by the window boundary.
- On Duty, Not Driving work may continue after the boundary.
- Before later driving, add a qualifying 10-hour reset.
- A 10-hour reset starts a new window when the next Driving or On Duty event begins.

Required invariant: no Driving minute occurs after the active window’s end.

## Rule 3: 30-minute break after 8 cumulative driving hours

After 8 cumulative hours (480 minutes) of Driving since the last qualifying non-driving period, the driver must complete at least 30 consecutive non-driving minutes before driving again.

Implementation requirements:

- The trigger is cumulative driving time, not elapsed shift time.
- Off Duty, Sleeper Berth, and On Duty, Not Driving can qualify.
- A 30-minute fuel event qualifies and resets driving-since-break.
- Pickup or another non-driving event qualifies when it lasts at least 30 consecutive minutes.
- Short nonconsecutive periods do not combine.
- The break does not reset the 11-hour total.
- The break does not pause or extend the 14-hour window.
- Use Off Duty for a standalone normal break.

Required invariant: driving-since-break never exceeds 480 minutes.

## Rule 4: 70-hour/8-day cycle

The legal rule is a rolling on-duty total. Both Driving and On Duty, Not Driving count; Off Duty and Sleeper Berth do not. Reaching the limit prohibits driving, but does not itself prohibit non-driving work.

### Assessment limitation

Only one prior-cycle total is supplied. The preceding eight individual daily totals are unknown, so exact daily recapture cannot be calculated.

Use this conservative bucket:

```text
initial cycle-used minutes =
    round(current_cycle_used_hours * 60)

available cycle minutes =
    4,200 - initial cycle-used minutes
```

Implementation requirements:

- Validate input between 0 and 70 hours inclusive.
- Preserve minute precision internally after converting the accepted decimal input.
- Add Driving, pickup, drop-off, and fuel minutes to modeled cycle usage.
- If the cycle boundary occurs while driving, stop at the boundary.
- If it is reached during pickup, fuel, drop-off, or another On Duty, Not Driving event, finish that event but prohibit later driving.
- When driving remains and the bucket blocks it, add a modeled 34-hour restart.
- After the restart, set cycle-used minutes to zero.

Required invariant: no Driving minute occurs while modeled cycle-used time is 4,200 minutes or more.

## Rule 5: Ten-hour reset

Ten consecutive hours (600 minutes) of Off Duty or Sleeper Berth resets:

- Driving since the 11-hour reset
- The active 14-hour driving window
- Driving since the last qualifying 30-minute break

It does not reset the modeled 70-hour cycle unless qualifying rest lasts at least 34 consecutive hours.

For normal overnight planning, emit a 600-minute Sleeper Berth event.

## Rule 6: 34-hour restart

FMCSA guidance describes the restart as optional and allows 34 or more consecutive hours Off Duty, Sleeper Berth, or a combination. Because exact rolling recapture is unavailable, this assessment deliberately schedules a restart when the conservative bucket is exhausted and driving remains.

Implementation requirements:

- Emit 2,040 consecutive minutes Off Duty.
- Reset modeled cycle usage to zero.
- Reset the 11-hour, 14-hour, and break clocks.
- Display the restart in the timeline, map, summary count, and daily logs.

The UI must not imply that every real driver is legally required to take a restart at cycle exhaustion.

## Operational events

### Pickup

- Begins when route progress reaches the pickup waypoint.
- Duration: 60 minutes.
- Status: On Duty, Not Driving.
- Counts toward the cycle and active 14-hour window.
- Qualifies as a 30-minute break.
- If it consumes the remaining driving window, rest before further driving.
- If it exhausts the cycle, finish pickup but do not drive afterward until restart.

### Drop-off

- Begins when route progress reaches the destination.
- Duration: 60 minutes.
- Status: On Duty, Not Driving.
- Counts toward the cycle.
- Completes the trip after its full duration.

### Fuel

- Plan before each additional 1,000 route miles, using 900 miles as the target interval.
- Duration: 30 minutes.
- Status: On Duty, Not Driving.
- Counts toward cycle usage and the active 14-hour window.
- Resets driving-since-break.
- Label as “Planned fuel stop along route” unless a POI source confirms an actual facility.

## Scheduler procedure

1. Start with normalized route progress, timezone-aware trip start, and modeled cycle usage.
2. Add driving only until the earliest next boundary:
   - Pickup/destination or another operational stop
   - 480-minute break limit
   - 660-minute driving limit
   - 14-hour window end
   - 4,200-minute modeled cycle limit
   - 900-mile fuel target
3. Add the required operational, break, sleeper, or restart event.
4. Update every affected clock and counter.
5. Continue until the full drop-off event is complete.
6. Build daily logs separately from the immutable final timeline.

Events must be ordered, contiguous where planned, timezone-aware, nonnegative, and minute-precise. Route progress and scheduled driving distance must be monotonic and reconcile to the provider route within a documented small tolerance.

## Event contract

Each event should expose at least:

```json
{
  "type": "driving | pickup | dropoff | fuel | rest_break | sleeper_berth | cycle_restart",
  "duty_status": "OFF_DUTY | SLEEPER_BERTH | DRIVING | ON_DUTY_NOT_DRIVING",
  "start_at": "ISO-8601 datetime",
  "end_at": "ISO-8601 datetime",
  "duration_minutes": 60,
  "distance_miles": 0,
  "coordinate": [-87.6298, 41.8781],
  "location_label": "Chicago, IL",
  "description": "Pickup"
}
```

Add a machine-readable reason for scheduler-created stops so the UI can explain the applicable constraint.

## Daily-log requirements

For each calendar day in the trip-start timezone:

- Split any event that crosses midnight.
- Cover midnight through midnight with no gaps or overlaps.
- Fill uncovered periods with Off Duty.
- Total all four duty statuses to exactly 1,440 minutes.
- Start the status graph at midnight and end it at the following midnight.
- Calculate miles from only the day’s Driving portions.
- Record a location and activity remark for each relevant status change.
- Use the supplied blank log image as the SVG background.
- Fill date, from/to, miles, demo driver/carrier/vehicle/shipping metadata, status totals, and calculable cycle recap.
- Disclose that identity/carrier/vehicle/shipping fields are demo metadata.

The FMCSA guide calls for date, total driving miles, vehicle identifiers, carrier, main office, signature/certification, co-driver if applicable, a consistent time base, remarks at status changes, four status totals summing to 24 hours, and shipping information. The assessment can populate only known/demo fields and must not imply a real driver certification.

## Minimum automated cases

1. Under 8 driving hours: no required break.
2. Nine driving hours: one qualifying 30-minute break.
3. Over 11 driving hours: a 10-hour reset and no daily driving-clock violation.
4. 14-hour window: no driving after the boundary.
5. Fuel before 1,000 miles; On Duty, Not Driving; resets break counter.
6. Starting at 69 cycle hours: stop at 70 and restart if driving remains.
7. Pickup/drop-off: exactly 60 minutes each and counted toward cycle.
8. Cross-midnight event splitting.
9. Every daily log totals 1,440 minutes with no gaps/overlaps.
10. Scheduled driving distance reconciles to route distance within tolerance.

Also test interactions: pickup near a window/cycle boundary, fuel near the break threshold, zero available cycle hours, simultaneous constraints, and final drop-off after driving eligibility ends.