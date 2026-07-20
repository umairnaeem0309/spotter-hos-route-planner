# Project Status

Last updated: 2026-07-21
Current branch: `feature/hos-engine` (Phase 3), stacked on
`feature/routing-provider` (Phase 2) / `feature/backend-foundation` (Phase 1),
all pushed.
Latest baseline commit: `6818803 Merge pull request #2 ...` (main)

## Current phase

Phase 3 — pure HOS scheduling engine (complete). Ready to begin Phase 4
(trip API and route progress).

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

## In progress

- None. Phase 3 acceptance met; awaiting Phase 4.

## Not started

- Trip API and route progress (Phase 4)
- Daily-log backend (Phase 5)
- React application and features (Phases 6–7)
- Automated frontend tests, production builds, deployment, and Loom (Phase 8)

## Validation results

- `python manage.py check` (development): no issues.
- `python manage.py check --deploy` (production, strong secret + hosts): no
  issues, no warnings.
- Production settings raise on missing/placeholder secret and empty
  `ALLOWED_HOSTS`.
- `pytest`: 54 passed (health, config safety, error schema, provider success
  and every failure mode, key-safe URL, and the full HOS engine suite).
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

Begin Phase 4 — trip API and route progress (backend):

- `services/route_progress.py`: build the scheduler's `DrivingLeg`s from a
  provider `Route` (segment 0 = current->pickup ending PICKUP, segment 1 =
  pickup->drop-off ending DROPOFF; meters->miles, seconds->rounded minutes).
  After scheduling, map each event's cumulative `meta` distance onto the route
  LineString to an approximate `coordinate`; prefer step geometry indexes, else
  interpolate by cumulative segment distance. Reverse-geocode stop coordinates
  best-effort, falling back to formatted lat/lon; label generated fuel points
  "Planned fuel stop along route".
- `api/serializers.py`: request validation — three non-blank locations,
  `current_cycle_used_hours` in [0, 70], optional ISO-8601 `trip_start`
  (default to now in a chosen tz); field-level 400s.
- `api/views.py`: `POST /api/trips/plan/` orchestrating geocode -> route ->
  schedule -> route-progress -> response contract (trip_id, input, summary,
  route{geometry,waypoints,instructions}, timeline, daily_logs=[] for now,
  assumptions, warnings). Keep scheduling out of the view.
- Tests: mocked geocoding/routing; assert the response contract, field-level
  validation errors, provider-failure mapping (502/503), and distance
  reconciliation of mapped coordinates within tolerance. At least one full API
  integration test.

Note: `daily_logs` stays empty until Phase 5. Trip start timezone handling and
the assumptions/warnings copy should reflect `docs/HOS_RULES.md`.

Acceptance: `POST /api/trips/plan/` returns the full contract for a mocked
route, validation and provider errors use the canonical schema, and all tests
pass without a live key.
