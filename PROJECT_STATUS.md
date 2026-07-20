# Project Status

Last updated: 2026-07-21
Current branch: `feature/daily-logs` (Phase 5), stacked on the Phase 1-4
branches, all pushed.
Latest baseline commit: `6818803 Merge pull request #2 ...` (main)

## Current phase

Phase 5 — daily-log backend (complete). The backend (Phases 1-5) is
functionally complete. Ready to begin Phase 6 (frontend foundation/features).

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

- Phase 5 daily-log backend (`services/daily_log_builder.py`):
  - Splits the timeline at midnight in the trip-start tz; prorates driving
    miles across split segments; fills Off-Duty gaps to exactly 1,440
    minutes/day with no gaps/overlaps.
  - Per-day status totals, driving miles, remarks (time/location/activity),
    modeled 70-hour recap, and demo metadata (flagged).
  - Wired into `build_trip_plan` `daily_logs`; `number_of_log_days` from the
    builder. `tests/test_daily_logs.py` (10 tests).

## In progress

- None. Phase 5 acceptance met; backend complete; awaiting Phase 6.

## Not started

- React application and features (Phase 6)
- Daily-log UI / SVG overlay (Phase 7)
- QA, deployment, screenshots, Loom (Phase 8)
- Daily-log backend (Phase 5)
- React application and features (Phases 6–7)
- Automated frontend tests, production builds, deployment, and Loom (Phase 8)

## Validation results

- `python manage.py check` (development): no issues.
- `python manage.py check --deploy` (production, strong secret + hosts): no
  issues, no warnings.
- Production settings raise on missing/placeholder secret and empty
  `ALLOWED_HOSTS`.
- `pytest`: 85 passed (health, config safety, error schema, provider layer,
  full HOS engine, route progress, trip-plan API, and daily-log builder).
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

Begin Phase 6 — React frontend foundation and core features (`frontend/`):

- Scaffold Vite + React + TypeScript + Tailwind under `frontend/` (feature-based
  structure per `docs/ARCHITECTURE.md`). Add `.env.example` with
  `VITE_API_BASE_URL`.
- `src/types/trip.ts`: strict TypeScript types mirroring the Django response
  contract (summary, route, timeline, daily_logs, assumptions, warnings).
- `src/api/client.ts` + `trips.ts`: fetch wrapper with `AbortController`
  (stale-request-safe) and typed error handling against the canonical error
  schema.
- `features/trip-form`: inputs (current/pickup/dropoff, cycle used, optional
  trip start), validation, empty/loading/error states, "Load sample trip".
- Summary metric cards, MapLibre + OpenFreeMap route map with markers/legend,
  timeline cards (with reason explanations), stops list, and route-instructions
  accordion. (Daily-log SVG is Phase 7.)
- Vitest + React Testing Library setup; tests for form validation, success
  render, and API-error render.

Notes: the map basemap style is `https://tiles.openfreemap.org/styles/liberty`;
retain attribution. Do not call ORS from the browser. Navy/teal/white/neutral
palette; responsive; accessible.

Acceptance: `npm run dev` serves the SPA; a mocked/live plan renders summary,
map, timeline, and instructions; type-check and the frontend tests pass.
