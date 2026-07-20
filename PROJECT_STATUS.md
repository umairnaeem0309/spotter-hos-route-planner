# Project Status

Last updated: 2026-07-21
Current branch: `feature/routing-provider` (Phase 2); Phase 1 on
`feature/backend-foundation` (pushed).
Latest baseline commit: `6818803 Merge pull request #2 ...` (main)

## Current phase

Phase 2 — routing provider foundation (complete). Ready to begin Phase 3
(pure HOS engine).

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

## In progress

- None. Phase 2 acceptance met; awaiting Phase 3.

## Not started

- HOS scheduling engine (Phase 3)
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
- `pytest`: 38 passed (health, config safety, error schema, provider success
  and every failure mode, key-safe URL).
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

Begin Phase 3 — pure HOS scheduling engine (`services/hos_scheduler.py`),
backend only, no HTTP/ORM/wall-clock dependencies:

- Consume a normalized `Route`, a fixed timezone-aware trip start, and
  `current_cycle_used_hours` to emit an ordered list of `TimelineEvent`s.
- Implement, per `docs/HOS_RULES.md`:
  - 11-hour driving limit (660 min) + 10-hour (600 min) sleeper reset.
  - 14-hour elapsed driving window (wall-clock; breaks do not extend it).
  - 30-minute break after 8 cumulative driving hours (480 min); fuel/pickup
    >= 30 min qualifies and resets the counter.
  - Conservative 70-hour cycle bucket (4,200 min) counting Driving +
    On-Duty-Not-Driving; 34-hour (2,040 min) Off-Duty restart when exhausted
    and driving remains.
  - 900-mile fuel interval (30-min On-Duty events).
  - 60-min pickup and 60-min drop-off, both On-Duty-Not-Driving.
- Attach machine-readable `reason_code`s to scheduler-created stops.
- Keep exact integer-minute precision and timezone-aware datetimes.

Add `tests/test_hos_scheduler.py` covering every case in HOS_RULES.md
"Minimum automated cases" plus the interaction cases. Use synthetic in-memory
`Route` fixtures (no network). Route-progress interpolation and reverse-geocode
labeling of stops belong to Phase 4; the scheduler may emit coordinate=None or
raw route coordinates for now.

Acceptance: all rule invariants hold in tests, no driving violates any limit,
and the scheduler is pure/deterministic for a fixed input.
