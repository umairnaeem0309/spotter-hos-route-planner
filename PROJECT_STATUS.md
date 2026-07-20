# Project Status

Last updated: 2026-07-21
Current branch: `feature/backend-foundation`
Latest baseline commit: `6818803 Merge pull request #2 from umairnaeem0309/setup/project-foundation`

## Current phase

Phase 1 — backend foundation (complete). Ready to begin Phase 2 (routing
provider foundation).

## Completed

- Phase 0 documentation foundation (merged to `main`).
- Initialized the Django project under `backend/` with a `config/` project
  package and an `apps/trips/` application package.
- Added Django REST Framework, django-cors-headers, pytest, pytest-django,
  whitenoise, requests, and gunicorn to `backend/requirements.txt`.
- Split settings into `base`, `development`, `production`, and `test` modules,
  loaded from the environment via django-environ.
- Production settings refuse to start on a missing or placeholder
  `DJANGO_SECRET_KEY` and require an explicit `ALLOWED_HOSTS`.
- Configured CORS from `CORS_ALLOWED_ORIGINS` / `FRONTEND_URL`.
- Defined the canonical safe API error schema and DRF exception handler.
- Implemented `GET /api/health/` returning `{"status": "ok"}`.
- Added health-endpoint and configuration-safety tests.

## In progress

- None. Phase 1 acceptance met; awaiting Phase 2.

## Not started

- OpenRouteService geocoding/routing clients (Phase 2)
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
  `ALLOWED_HOSTS` (verified via tests and manual check).
- `pytest`: 9 passed.
- Live boot: dev server started; `GET /api/health/` returned HTTP 200 and
  `{"status": "ok"}` with security headers.
- Secret scan: no `.env` or credentials committed; `.venv/`, `db.sqlite3`,
  `staticfiles/` are git-ignored.

## Known blockers

- `ORS_API_KEY` is required before live geocoding/routing (Phase 2 live calls
  and manual route testing). Not needed for Phase 2 mocked tests.
- Deployment URLs/credentials not needed yet.

## Exact next task

Begin Phase 2 — routing provider foundation (backend only):

- Add `apps/trips/types.py` domain types (coordinates, duty status, event
  type) as needed by the provider layer.
- Implement `apps/trips/services/geocoding.py` (Pelias search + reverse) and
  `apps/trips/services/routing.py` (`driving-hgv` GeoJSON directions through
  current -> pickup -> drop-off) calling OpenRouteService only from Django.
- Define typed provider errors (missing key, invalid address, no route,
  rate limit, timeout, upstream failure) subclassing `ApiError` so the existing
  safe exception handler renders them with correct HTTP status (502/503).
- Add request timeouts and sanitized logging that never leaks the API key.
- Add mocked provider unit tests; never require a live key in automated tests.

Acceptance: provider clients parse valid responses, raise the correct typed
errors on each failure mode, never log/leak the key, and all tests pass with
external calls mocked.
