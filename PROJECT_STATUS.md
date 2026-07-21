# Project Status

Last updated: 2026-07-21
Current branch: `feature/frontend-foundation` (Phase 6), stacked on the
Phase 1-5 branches, all pushed.
Latest baseline commit: `6818803 Merge pull request #2 ...` (main)

## Current phase

Phase 6 — frontend foundation and features (complete). Ready to begin Phase 7
(daily-log SVG UI).

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

- Phase 6 React frontend (`frontend/`, Vite + TS + Tailwind + MapLibre):
  - Strict types (`types/trip.ts`) mirroring the API; stale-safe client
    (`api/client.ts` with AbortController + typed `ApiError`), `api/trips.ts`.
  - Trip form with client validation, server field-error mapping, empty/
    loading/error states, and the three acceptance samples.
  - Summary cards, MapLibre + OpenFreeMap map with waypoint/stop markers and a
    legend, HOS timeline (with reason explanations), route-instructions
    accordion, assumptions + warnings panel.
  - `TripPlannerPage` state machine; responsive two-column layout; footer
    disclaimer + attribution.
  - Vitest + RTL: `TripForm.test.tsx`, `TripPlannerPage.test.tsx` (8 tests).
  - Type-check clean; production build succeeds.

## In progress

- None. Phase 6 acceptance met; awaiting Phase 7.

## Not started

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
- Frontend `tsc --noEmit`: clean. `vitest run`: 8 passed. `npm run build`:
  succeeds (bundle ~272 kB gzip, maplibre-dominated; noted for Phase 8).
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

Begin Phase 7 — daily-log SVG UI (`frontend/src/features/logs/`):

- `logTemplateCoordinates.ts`: centralized x/y coordinates for the blank log
  template (grid start/end X, the four duty-status row Y positions, field
  positions). No scattered pixel constants elsewhere.
- `DailyLogSheet.tsx`: SVG `viewBox` with `/assets/blank-paper-log.png` as an
  `<image>` background. Draw a continuous 24-hour duty-status polyline
  (time-to-x: `gridStartX + (minutesFromMidnight/1440)*(gridEndX-gridStartX)`),
  horizontal status runs + vertical connectors, status totals on the right,
  fields (date, from/to, miles, demo driver/carrier/office/vehicle/shipping),
  and remarks beneath. Disclose demo metadata.
- Multi-log navigation (tabs or prev/next), a "Print logs" action with print
  CSS (one sheet per page), and a dev-only calibration grid toggle.
- Wire `daily_logs` from the plan into the results view.
- Tests: minute-to-x positioning for a known segment, and multi-log navigation.

Note: verify the SVG overlay visually aligns to the supplied
`blank-paper-log.png` (518x518 assumed; confirm actual dimensions and set the
viewBox/coordinates accordingly).

Acceptance: log sheets render on the template, the graph aligns to the grid,
multiple days navigate, printing yields one sheet per page, and tests pass.
