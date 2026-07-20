# HOS Route Planner

A time-boxed full-stack assessment that will plan a current → pickup → drop-off truck route, apply a defined property-carrying Hours of Service model, and generate one completed driver daily log for each trip calendar day.

> Status: repository and documentation foundation only. The Django and React applications have not been created yet.

## Deliverable links

- Hosted frontend: _TBD_
- Backend API: _TBD_
- Loom walkthrough: _TBD_
- GitHub repository: _TBD_

## Screenshots

Screenshots will be added after the first complete UI flow is implemented.

## Planned user flow

1. Enter current, pickup, and drop-off locations.
2. Enter current hours used in the 70-hour/8-day cycle.
3. Optionally select a timezone-aware trip start for reproducible results.
4. Generate a route, compliant schedule, operational-stop map, instructions, and daily logs.
5. Review or print one log sheet per calendar day.

## Architecture

The monorepo will use:

- **Backend:** Django, Django REST Framework, OpenRouteService clients, pure HOS services, and pytest
- **Frontend:** React, Vite, TypeScript, Tailwind CSS, MapLibre GL JS, and Vitest/React Testing Library
- **Map:** OpenFreeMap’s Liberty style, rendered by MapLibre with attribution
- **Security boundary:** React calls Django; only Django calls OpenRouteService

The backend will own validation, provider integration, scheduling, route progress, and daily-log data. The frontend will own interaction and visualization, including an SVG overlay on the supplied blank log image.

See [Architecture](docs/ARCHITECTURE.md), [HOS rules](docs/HOS_RULES.md), and [decisions](DECISIONS.md).

## Repository layout

```text
backend/                         # Django project (next phase; not initialized)
frontend/                        # React project (not initialized)
  public/assets/blank-paper-log.png
docs/
  ARCHITECTURE.md
  HOS_RULES.md
  MASTER_IMPLEMENTATION_SPEC.md
  references/
AGENTS.md
PROJECT_CONTEXT.md
PROJECT_STATUS.md
TASKS.md
DECISIONS.md
HANDOFF.md
```

## Technology choices

The stack is fixed by the assessment:

- Python, Django, Django REST Framework
- React, Vite, TypeScript, Tailwind CSS
- MapLibre GL JS and OpenFreeMap
- OpenRouteService `driving-hgv`, geocoding, and reverse geocoding
- pytest; Vitest and React Testing Library

## Local setup

The exact install commands and lockfiles will be added when each application is scaffolded. Do not assume the commands below work until Phase 1/Phase 6 creates the relevant files.

### Backend target workflow

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item ..\.env.example .env
python manage.py migrate
python manage.py runserver
```

### Frontend target workflow

```powershell
cd frontend
npm install
npm run dev
```

Never place `ORS_API_KEY` in a `VITE_*` variable or frontend source.

## Environment variables

Copy `.env.example` to an ignored local `.env` only after the backend exists.

| Variable | Consumer | Purpose |
| --- | --- | --- |
| `ORS_API_KEY` | Django | OpenRouteService credential |
| `DJANGO_SECRET_KEY` | Django | Django cryptographic secret |
| `DEBUG` | Django | Explicit development/production mode |
| `ALLOWED_HOSTS` | Django | Comma-separated host allowlist |
| `CORS_ALLOWED_ORIGINS` | Django | Comma-separated browser origin allowlist |
| `FRONTEND_URL` | Django | Canonical deployed frontend URL |
| `VITE_API_BASE_URL` | React | Public Django API base URL; never contains secrets |

Production must use `DEBUG=false`, a strong `DJANGO_SECRET_KEY`, exact allowed hosts/origins, and HTTPS URLs.

## Planned API

### Health

```http
GET /api/health/
```

```json
{"status": "ok"}
```

### Trip plan

```http
POST /api/trips/plan/
Content-Type: application/json
```

```json
{
  "current_location": "Chicago, IL",
  "pickup_location": "Indianapolis, IN",
  "dropoff_location": "Dallas, TX",
  "current_cycle_used_hours": 18.5,
  "trip_start": "2026-07-20T08:00:00-05:00"
}
```

The response will contain normalized input, summary metrics, GeoJSON route geometry, waypoints, instructions, a chronological event timeline, daily logs, assumptions, and warnings. Field validation errors return 400; safe provider failures return 502/503.

## HOS rules to implement

- 11-hour driving limit after a qualifying 10-hour reset
- 14-consecutive-hour elapsed driving window
- 30 consecutive non-driving minutes after 8 cumulative driving hours
- 70-hour/8-day modeled cycle limit
- Ten-hour Sleeper Berth daily resets
- 34-hour Off Duty modeled cycle restart when required by the conservative plan
- Driving and On Duty, Not Driving count toward cycle usage
- One-hour pickup and drop-off as On Duty, Not Driving
- Thirty-minute On Duty, Not Driving fuel stops at 900-mile planning intervals
- Full 24-hour logs using the trip-start timezone

The complete implementation contract is in [docs/HOS_RULES.md](docs/HOS_RULES.md).

## Important assumptions and limitation

The assessment provides the total current cycle hours but not the driver's individual duty totals for the previous eight days. Therefore, the application cannot calculate exact rolling recapture hours. It uses the supplied cycle total as a conservative bucket and schedules a 34-hour restart when that bucket is exhausted.

The model also excludes adverse-driving, short-haul, personal-conveyance, split-sleeper, and team-driver calculations. Generated fuel points are planned positions along the route, not claims that a real truck stop exists. All logs use the trip-start timezone.

This application is an assessment/demo planner, not a certified ELD or legal-compliance product.

## Daily logs

The frontend must use `frontend/public/assets/blank-paper-log.png` as the visual background. A reusable SVG overlay will draw the four duty-status rows, vertical transitions, totals, known metadata, and location remarks. Each log must contain exactly 1,440 minutes with no gaps or overlaps.

## Testing

Planned commands after scaffolding:

```powershell
cd backend
pytest
```

```powershell
cd frontend
npm test -- --run
npm run build
```

Tests must cover the scheduling edge cases, calendar splitting, route progress, API validation/provider failures, form states, multiple-log navigation, and known SVG positioning.

## Deployment target

- **Frontend:** Vercel, root `frontend`, build `npm run build`, output `dist`
- **Backend:** Render or equivalent, root `backend`, migrations during build, Gunicorn start command
- Configure `VITE_API_BASE_URL` to the hosted backend’s `/api` URL.
- Add the hosted frontend origin to Django CORS settings.
- Verify hosted `GET /api/health/` and `POST /api/trips/plan/` before delivery.

Deployment files and exact commands will be added after the applications exist.

## Reference material

- Assessment: `docs/references/new-full-stack-dev-assessment.docx`
- FMCSA guide: `docs/references/fmcsa-hos-driver-guide.pdf`
- FMCSA TOC: `docs/references/fmcsa-toc.png`
- Log template: `frontend/public/assets/blank-paper-log.png`

The April 2022 FMCSA guide is guidance and explicitly says it is not a substitute for the regulations.