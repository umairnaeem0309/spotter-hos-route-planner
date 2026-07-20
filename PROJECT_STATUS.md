# Project Status

Last updated: 2026-07-21
Current branch: `feature/trip-api` (Phase 4), stacked on the Phase 1-3
branches, all pushed.
Latest baseline commit: `6818803 Merge pull request #2 ...` (main)

## Current phase

Phase 4 — trip API and route progress (complete). Ready to begin Phase 5
(daily-log backend).

## Completed

- Phase 0 documentation foundation (merged to `main`).
- Phase 1 backend foundation: Django project (`config/`) + `apps/trips/`,
  split env-driven settings, fail-safe production, CORS, safe error schema,
  `GET /api/health/`, and tests.
- Phase 2 provider foundation:
  - `apps/trips/types.py`: framework-free domain types (Coordinate, DutyStatus,
    EventType, Route/RouteSegment/RouteStep, GeocodedLocation, TimelineEvent).
  - `services/errors.py`: typed provider errors subclassing `ApiError`
    (not-configured, address-not-found, no-route, rate-limited, timeout,
    unavailable) with correct 400/502/503 mapping.
  - `services/ors_client.py`: single external-request choke point with a
    settings-driven timeout, transport/transient error mapping, and key-safe
    logging (query strings stripped before logging).
  - `services/geocoding.py`: Pelias search + reverse (best-effort, returns
    None on miss).
  - `services/routing.py`: `driving-hgv` GeoJSON directions through ordered
    waypoints, normalized into `Route`.
  - Refined the exception handler so typed 400s keep their code and only DRF
    ValidationErrors are relabeled `validation_error`.

- Phase 3 pure HOS engine (`services/hos_scheduler.py`):
  - `_Planner` state machine + `plan_trip(legs, trip_start, cycle_hours)`.
  - Provider-agnostic input via `DrivingLeg` (added to `types.py`).
  - 11-hour limit + 10-hour sleeper reset; 14-hour elapsed window; 8-hour /
    30-min break; conservative 70-hour bucket + 34-hour restart; 900-mile fuel
    (fuel prioritized over standalone break so coincident stops merge).
  - Pickup/drop-off = 60 min On-Duty; contiguous integer-minute events with
    machine-readable `reason_code`s and cumulative route distance in `meta`.
  - `ScheduleResult` with summary counts (fuel/break/sleeper/restart).
  - 16 scheduler tests: every HOS_RULES.md minimum case + interactions,
    determinism, distance reconciliation, invariant checker.

- Phase 4 trip API and route progress:
  - `services/route_progress.py`: `build_driving_legs` (Route -> DrivingLegs)
    and `apply_route_progress` (map events to route coords via cumulative
    haversine interpolation; exact waypoint coords/labels; best-effort reverse
    geocode with lat/lon fallback; fuel labeled as planned point).
  - `api/serializers.py`: `TripPlanRequestSerializer` with field-level
    validation and offset-preserving ISO-8601 `trip_start` parsing.
  - `services/trip_planner.py`: `build_trip_plan` orchestration + assumptions
    and warnings copy.
  - `api/views.py` + `urls.py`: `POST /api/trips/plan/` (thin view).
  - `tests/test_api.py` (integration, mocked providers) and
    `tests/test_route_progress.py`.

## In progress

- None. Phase 4 acceptance met; awaiting Phase 5.

## Not started

- Daily-log backend (Phase 5)
- Daily-log backend (Phase 5)
- React application and features (Phases 6–7)
- Automated frontend tests, production builds, deployment, and Loom (Phase 8)

## Validation results

- `python manage.py check` (development): no issues.
- `python manage.py check --deploy` (production, strong secret + hosts): no
  issues, no warnings.
- Production settings raise on missing/placeholder secret and empty
  `ALLOWED_HOSTS`.
- `pytest`: 75 passed (health, config safety, error schema, provider layer,
  full HOS engine, route progress, and the trip-plan API integration tests).
- Live boot: dev server started; `GET /api/health/` returned HTTP 200 and
  `{"status": "ok"}` with security headers.
- Secret scan: no `.env` or credentials committed; `.venv/`, `db.sqlite3`,
  `staticfiles/` are git-ignored.

## Known blockers

- `ORS_API_KEY` is required before live geocoding/routing (real routes,
  manual acceptance tests, deployment). All automated tests mock the provider
  and need no key. The user does not have a key yet; free signup documented in
  `backend/.env.example`.
- Deployment URLs/credentials not needed yet.

## Exact next task

Begin Phase 5 — daily-log backend (`services/daily_log_builder.py`):

- Split the immutable timeline into calendar days in the trip-start timezone;
  split any event crossing midnight into per-day segments (preserve exact
  minutes; prorate driving miles across split driving segments).
- For each day: fill uncovered time with Off Duty so the four duty-status
  totals sum to exactly 1,440 minutes with no gaps/overlaps.
- Compute per-day: date, from/to labels, total driving miles (that day only),
  the four status totals, remarks (time + nearest location + activity) at each
  relevant status change, and a modeled 70-hour recap.
- Add demo metadata (driver/carrier/office/vehicle/shipping) flagged as demo.
- Wire the result into `build_trip_plan` `daily_logs` and set
  `summary.number_of_log_days` from the builder output.
- Add `tests/test_daily_logs.py`: cross-midnight splits, gap/overlap filling,
  exactly-1,440-minute totals, per-day miles, and remark generation.

Acceptance: every generated day totals exactly 1,440 minutes with no gaps or
overlaps, cross-midnight events split correctly, and the daily logs appear in
the trip-plan response. All tests pass.
