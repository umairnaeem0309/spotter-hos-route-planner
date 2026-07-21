# HOS Route Planner

**Property-Carrying Driver Trip & ELD Log Planner** — a full-stack demonstration
app that plans a truck route through *current → pickup → drop-off*, schedules a
Hours-of-Service (HOS) compliant timeline (driving limits, breaks, fueling, and
rest), and generates a completed driver daily-log sheet for every calendar day.

> **Disclaimer.** This is a time-boxed assessment/demo planner, **not** a
> certified ELD or a legal-compliance product. See *Known limitations*.

## Links

- Hosted frontend: _`<add Vercel URL>`_
- Backend API: _`<add Render URL>`_ (health: `/api/health/`)
- Loom walkthrough: _`<add Loom URL>`_
- Repository: https://github.com/umairnaeem0309/spotter-hos-route-planner

## Screenshots

_Add screenshots after deployment:_

- `docs/screenshots/planner.png` — form + summary + map
- `docs/screenshots/timeline.png` — HOS timeline
- `docs/screenshots/daily-log.png` — daily-log sheet

## Overview

Enter a current location, pickup, drop-off, and current 70-hour-cycle usage
(optionally a fixed trip start). The app returns:

- an interactive route map with markers for the stops, fuel, breaks, sleeper
  rests, and any 34-hour restart;
- summary metrics (distance, raw vs. compliant duration, arrival, counts);
- a chronological HOS-compliant schedule with plain-language reasons;
- turn-by-turn directions; and
- one ELD daily-log sheet per calendar day, drawn on the supplied blank
  paper-log template.

## Architecture

```
React SPA (Vite + TS + Tailwind + MapLibre)
   │  POST /api/trips/plan/
   ▼
Django + DRF
   ├─ api/            validation, thin views, safe error schema
   └─ services/       geocoding · routing · hos_scheduler · route_progress · daily_log_builder
         │
         ▼  OpenRouteService (HeiGIT)  — geocoding + driving-hgv routing (server-side only)
```

- **Django** owns geocoding, routing-provider calls, HOS scheduling, route
  progress, and daily-log construction. The `ORS_API_KEY` never reaches the
  browser and never appears in responses or logs.
- **React** owns input, map rendering, timeline, daily-log SVG overlays,
  printing, and all user-facing states.
- HOS scheduling and daily-log building are **pure, deterministic, unit-tested**
  services with no HTTP/ORM/wall-clock dependency.

See `docs/ARCHITECTURE.md`, `docs/HOS_RULES.md`, and `DECISIONS.md`.

## Technology choices

| Area | Choice |
| --- | --- |
| Backend | Django 5, Django REST Framework |
| Frontend | React 18, Vite, TypeScript, Tailwind CSS |
| Map | MapLibre GL JS + OpenFreeMap (`liberty` style) |
| Routing / geocoding | OpenRouteService (HeiGIT), server-side only |
| Backend tests | pytest / pytest-django |
| Frontend tests | Vitest + React Testing Library |
| Serving | Gunicorn + WhiteNoise (backend), Vercel static (frontend) |

## Local setup

Requires Python 3.12+, Node 20+, and (for live routing) a free OpenRouteService
API key from <https://openrouteservice.org/dev/#/signup>.

### Backend

```bash
cd backend
python -m venv .venv
# Windows:  .venv\Scripts\activate       (bash: source .venv/Scripts/activate)
pip install -r requirements.txt
cp .env.example .env          # then edit .env (see below)
python manage.py runserver     # http://127.0.0.1:8000/api/health/
```

`manage.py` defaults to `config.settings.development`. Automated tests use
`config.settings.test`; production uses `config.settings.production`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local     # set VITE_API_BASE_URL if not the default
npm run dev                    # http://localhost:5173
```

## Environment variables

### Backend (`backend/.env`)

| Variable | Purpose |
| --- | --- |
| `DJANGO_SECRET_KEY` | Django secret. Production refuses placeholder/`django-insecure-` values. |
| `DEBUG` | `true` locally, `false` in production. |
| `ALLOWED_HOSTS` | Comma-separated hosts (required in production). |
| `CORS_ALLOWED_ORIGINS` | Comma-separated allowed frontend origins. |
| `FRONTEND_URL` | Primary frontend origin (default CORS origin). |
| `ORS_API_KEY` | OpenRouteService key (server-side only; never exposed). |

### Frontend (`frontend/.env.local`)

| Variable | Purpose |
| --- | --- |
| `VITE_API_BASE_URL` | Base URL of the API incl. `/api` (e.g. `http://localhost:8000/api`). Public config, not a secret. |

## API

### `POST /api/trips/plan/`

Request:

```json
{
  "current_location": "Chicago, IL",
  "pickup_location": "Indianapolis, IN",
  "dropoff_location": "Dallas, TX",
  "current_cycle_used_hours": 18.5,
  "trip_start": "2026-07-20T08:00:00-05:00"
}
```

`trip_start` is optional (defaults to now). Validation: locations must be
non-blank, `current_cycle_used_hours` in [0, 70], `trip_start` valid ISO-8601.

Response (abridged):

```json
{
  "trip_id": "uuid",
  "input": { "...": "normalized input" },
  "summary": {
    "total_distance_miles": 0, "raw_driving_minutes": 0,
    "compliant_trip_minutes": 0, "departure_at": "", "arrival_at": "",
    "number_of_log_days": 0, "fuel_stop_count": 0, "rest_break_count": 0,
    "overnight_rest_count": 0, "cycle_restart_count": 0
  },
  "route": { "geometry": { "type": "LineString", "coordinates": [] },
             "waypoints": [], "instructions": [] },
  "timeline": [ { "type": "driving", "duty_status": "DRIVING", "start_at": "",
                  "end_at": "", "duration_minutes": 0, "distance_miles": 0,
                  "coordinate": [0,0], "location_label": "", "reason_code": "" } ],
  "daily_logs": [ { "date": "", "segments": [], "totals": {}, "remarks": [] } ],
  "assumptions": [], "warnings": []
}
```

Errors use one schema: `{ "error": { "code", "message", "details?" } }` —
`400` for validation/address/no-route, `502`/`503` for provider failures.

### `GET /api/health/` -> `{ "status": "ok" }`

## HOS rules implemented

- **11-hour driving limit** after a qualifying 10-hour rest.
- **14-hour driving window** (elapsed wall-clock; breaks don't extend it).
- **30-minute break** after 8 cumulative driving hours (fuel or pickup >= 30 min
  qualifies).
- **70-hour / 8-day cycle** (Driving + On-Duty count); driving stops at the
  limit.
- **10-hour reset** (sleeper) resets the daily clocks; **34-hour restart**
  resets the modeled cycle.
- **Fueling** planned ~every 900 route miles (30 min, On Duty, satisfies the
  break).
- Pickup and drop-off are **60 minutes each, On Duty (Not Driving)**.

Full contract and sources: `docs/HOS_RULES.md`.

## Important assumptions

Property-carrying CMV, interstate, 70-hour/8-day; driver starts after 10 h off;
single trip timezone for all logs; no adverse-driving/short-haul/personal-
conveyance/split-sleeper/team logic. The full list is shown in-app under
**Calculation assumptions** and lives in
`backend/apps/trips/services/trip_planner.py`.

### The conservative 70-hour calculation

> The assessment provides the total current cycle hours but not the driver's
> individual duty totals for the previous eight days. Therefore, the application
> cannot calculate exact rolling recapture hours. It uses the supplied cycle
> total as a conservative bucket (`available = 70 - current cycle used`) and
> schedules a 34-hour restart when that bucket is exhausted and driving remains.

## Known limitations

- Not a certified ELD; no legal guarantee. Modeled cycle is conservative (above).
- Fuel/rest coordinates are interpolated along the route and labeled as *planned*
  points, not confirmed truck stops.
- Reverse geocoding for generated stops is best-effort with a lat/lon fallback.
- Single trip timezone even across timezone boundaries.
- The frontend JS bundle is MapLibre-dominated (~270 kB gzip); could be
  code-split for a smaller initial load.
- Daily-log identity/carrier/vehicle/shipping values are demo metadata.

## Tests

```bash
# Backend (85 tests)
cd backend && pytest

# Frontend (18 tests) + type-check + production build
cd frontend && npm test && npm run typecheck && npm run build
```

Backend coverage includes every HOS rule and interaction, daily-log invariants
(exactly 1,440 min/day, no gaps/overlaps, cross-midnight splits), the trip-plan
API (mocked provider), and configuration safety. See `docs/TEST_CASES.md`.

## Deployment

**Backend (Render).** Blueprint at `backend/render.yaml`: root `backend`, build
installs requirements + `collectstatic` + `migrate`, start with Gunicorn. Set
`ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `FRONTEND_URL`, and `ORS_API_KEY`
(confirm the generated `DJANGO_SECRET_KEY`).

**Frontend (Vercel).** Root `frontend`, build `npm run build`, output `dist`
(`frontend/vercel.json` included). Set `VITE_API_BASE_URL` to
`https://<backend-domain>/api`. Ensure the Vercel origin is in the backend's
`CORS_ALLOWED_ORIGINS`.

## Manual acceptance trips

Provided as one-click samples in the form (also in `docs/TEST_CASES.md`):

- **A** Chicago -> Indianapolis -> Nashville, cycle 5 — one log day.
- **B** New York -> Pittsburgh -> Los Angeles, cycle 10 — multiple sleepers/fuel.
- **C** Chicago -> Milwaukee -> Dallas, cycle 69 — 34-hour restart.
- **D** An invalid address — helpful error, no crash.
