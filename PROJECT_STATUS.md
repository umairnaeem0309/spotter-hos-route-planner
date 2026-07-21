# Project Status

Last updated: 2026-07-21
Current branch: `feature/daily-log-ui` (Phase 7), stacked on the Phase 1-6
branches, all pushed.
Latest baseline commit: `6818803 Merge pull request #2 ...` (main)

## Current phase

Phase 7 — daily-log SVG UI (complete). Only Phase 8 remains (QA, deployment
config, docs, screenshots, Loom).

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

- Phase 7 daily-log SVG UI (`frontend/src/features/logs/`):
  - `logTemplateCoordinates.ts`: centralized, pixel-calibrated coordinates
    (24-hour grid x=80..470, rows at y=191/209/226/244) + `minuteToX`.
  - `DailyLogSheet.tsx`: SVG overlay on `blank-paper-log.png` with a continuous
    24-hour duty-status polyline, per-row totals, header/identity fields,
    remarks, modeled recap, demo-metadata disclosure, and a dev calibration
    grid.
  - `DailyLogs.tsx`: multi-day tabs + prev/next, "Print logs" with one-sheet-
    per-page print CSS, dev-only calibration toggle, accessible totals table.
  - Wired into the results view. Tests: `logTemplateCoordinates.test.ts`,
    `DailyLogs.test.tsx` (10 more; 18 frontend total).
  - Overlay alignment verified by compositing the graph over the template.

## In progress

- None. Phase 7 acceptance met; awaiting Phase 8.

## Not started

- QA, deployment config, screenshots, Loom (Phase 8)
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
- Frontend `tsc --noEmit`: clean. `vitest run`: 18 passed. `npm run build`:
  succeeds (bundle ~274 kB gzip, maplibre-dominated; noted for Phase 8).
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

Begin Phase 8 — quality and delivery:

- Deployment config: `backend/render.yaml` (or equivalent) — build installs
  requirements + runs migrations + collectstatic; start with Gunicorn on
  `config.wsgi`. Frontend Vercel config (root `frontend`, build `npm run build`,
  output `dist`, `VITE_API_BASE_URL`). Document the production env vars.
- Rewrite the root `README.md` to the spec's required sections (overview,
  screenshots placeholders, architecture, setup, env vars, API example/overview,
  HOS rules, assumptions, the conservative-70h explanation, limitations, test
  commands, deployment, and link placeholders).
- Add `docs/LOOM_SCRIPT.md` and `docs/TEST_CASES.md`.
- Run the full backend suite and the frontend test + typecheck + build.
- Manual acceptance A-D: needs a live `ORS_API_KEY` in `backend/.env` and both
  servers running. Blocked until the user provides a key; document the steps so
  they can run them, and note it in "Known blockers".
- Optional: code-split MapLibre to shrink the initial bundle.

Acceptance: deployment files present, README + docs complete, all automated
tests/build green. Live acceptance trips + deployment + Loom recording require
the ORS key and hosting credentials from the user.
