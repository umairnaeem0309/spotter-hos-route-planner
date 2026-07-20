# Architecture Plan

## Purpose and boundaries

The application is a stateless trip-planning demonstration with two deployable applications:

- Django validates input, calls OpenRouteService, schedules HOS events, maps events to route progress, and builds daily-log data.
- React collects input and renders the returned plan as summary metrics, a MapLibre map, timeline, instructions, and SVG daily logs.

OpenRouteService is never called by browser code. Authentication, fleet management, payments, and unrelated administration are outside scope.

## System flow

```text
React trip form
    |
    | POST /api/trips/plan/
    v
Django API validation
    |
    +--> geocode current / pickup / drop-off
    +--> request driving-hgv route
    +--> pure HOS scheduler
    +--> route-progress interpolation
    +--> daily-log builder
    |
    v
Typed trip-plan response
    |
    +--> summary and warnings
    +--> MapLibre route and markers
    +--> timeline and instructions
    +--> SVG daily-log sheets
```

## Planned repository structure

```text
backend/
  config/
    settings/
    urls.py
    wsgi.py
  apps/trips/
    api/
      serializers.py
      urls.py
      views.py
    services/
      geocoding.py
      routing.py
      hos_scheduler.py
      route_progress.py
      daily_log_builder.py
    tests/
      test_api.py
      test_daily_logs.py
      test_hos_scheduler.py
      test_route_progress.py
    types.py

frontend/
  public/assets/
    blank-paper-log.png
  src/
    api/
      client.ts
      trips.ts
    components/
      ui/
      ErrorState.tsx
      LoadingState.tsx
    features/
      trip-form/
      map/
      timeline/
      route-instructions/
      logs/
        components/DailyLogSheet.tsx
        logTemplateCoordinates.ts
    pages/TripPlannerPage.tsx
    types/trip.ts
    App.tsx
    main.tsx
```

Names may be adjusted during scaffolding, but the dependency boundaries below are fixed.

## Backend boundaries

### API layer

Responsibilities:

- Deserialize and validate locations, cycle hours, and optional ISO-8601 trip start.
- Coordinate service calls.
- Translate typed provider/domain errors into a consistent safe response.
- Return the documented response contract.

The API layer must not contain scheduling calculations.

### Provider clients

`geocoding.py` and `routing.py` will:

- Read `ORS_API_KEY` only from backend configuration.
- Use explicit request timeouts.
- Request the `driving-hgv` route through all three ordered waypoints.
- Preserve GeoJSON geometry, segment/step distance, duration, and instructions.
- Raise typed errors for missing keys, invalid addresses, rate limits, no route, timeout, and upstream failure.
- Avoid logging secrets or unsafe full provider payloads.

Provider calls are mocked in automated tests.

### Domain types

Use explicit typed values for:

- Coordinates as `[longitude, latitude]`
- Duty status: `OFF_DUTY`, `SLEEPER_BERTH`, `DRIVING`, `ON_DUTY_NOT_DRIVING`
- Event type: driving, pickup, dropoff, fuel, rest break, sleeper berth, cycle restart
- Route progress and trip summary
- Daily status segments, totals, miles, remarks, and modeled cycle recap

Datetimes are timezone-aware. Durations remain integer minutes internally.

### Pure HOS scheduler

`hos_scheduler.py` accepts normalized route/waypoint progress, a fixed trip start, and current cycle usage. It emits an ordered event list without HTTP, ORM, filesystem, or wall-clock dependencies.

Scheduler state includes:

- Current timestamp and route progress
- Driving since qualifying break
- Driving since ten-hour reset
- Start/end of the active 14-hour window
- Modeled cycle-used minutes
- Distance since fuel
- Whether pickup/drop-off has been completed

At each driving step, advance only to the earliest next boundary: waypoint/destination, required break, 11-hour limit, 14-hour-window limit, cycle limit, or fuel interval. Add the required non-driving event, update state, and continue. See `docs/HOS_RULES.md`.

### Route progress

`route_progress.py` maps event distance/time progress onto the route:

1. Prefer provider step durations and geometry indexes.
2. Otherwise interpolate over LineString segment distances.
3. Reverse-geocode generated stop coordinates when practical.
4. Fall back to formatted coordinates.
5. Never identify a planned point as a real truck stop without POI evidence.

### Daily-log builder

`daily_log_builder.py` will:

- Split events at midnight in the trip-start timezone.
- Fill uncovered time with Off Duty.
- Guarantee ordered, gap-free, non-overlapping coverage of exactly 1,440 minutes.
- Prorate driving distance across split driving segments.
- Calculate four status totals and relevant cycle recap values.
- Add a location/activity remark at each relevant status change.
- Add Off Duty through the end of the final calendar day.

## API contract

### `GET /api/health/`

Returns HTTP 200:

```json
{"status": "ok"}
```

### `POST /api/trips/plan/`

Validates:

- Three nonblank location strings
- `current_cycle_used_hours` between 0 and 70 inclusive
- Optional valid timezone-aware ISO-8601 `trip_start`

Returns:

- `trip_id` and normalized input
- Summary distance, raw/compliant duration, departure/arrival, log/stop counts
- GeoJSON route, waypoints, and instructions
- Ordered timeline
- Ordered daily logs
- Assumptions and warnings

Use field-level HTTP 400 validation errors. Use safe HTTP 502/503 responses for routing-provider failures. Define one consistent error body during API foundation work.

## Frontend boundaries

- Keep API request code and types independent of presentation components.
- Use `AbortController` to prevent stale requests from replacing newer results.
- Keep MapLibre route/marker setup inside the map feature.
- Centralize log-template coordinates; do not scatter pixel constants.
- Use an SVG `viewBox` with the supplied PNG as the background.
- Include empty, loading, validation, provider-error, and success states.
- Preserve accessible labels, keyboard behavior, responsive layout, map attribution, and print CSS.

Only `VITE_API_BASE_URL` is exposed to the frontend. It is public configuration, not a credential.

## Configuration and security

Backend variables:

- `ORS_API_KEY`
- `DJANGO_SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `CORS_ALLOWED_ORIGINS`
- `FRONTEND_URL`

Frontend variable:

- `VITE_API_BASE_URL`

Production must reject insecure placeholder secrets, run with `DEBUG=false`, use exact host/origin allowlists, and sanitize provider errors/logging. Local `.env` files remain ignored.

## Testing strategy

### Backend

- Pure unit tests for every scheduling rule and interaction
- Invariants: nonnegative duration/distance, monotonic time/progress, no illegal driving, total route distance within tolerance
- Daily-log invariants: exactly 1,440 minutes, no gaps/overlaps, correct cross-midnight miles
- Mocked provider tests
- At least one API integration test

### Frontend

- Form validation and request states
- Successful summary/map/timeline/log rendering
- Provider-error presentation
- Multiple-log navigation
- Known minute-to-x SVG positioning
- Production type check and build

## Deployment plan

- Frontend: Vercel with `frontend` as root and `dist` output.
- Backend: Render or equivalent with `backend` as root, migrations in build, and Gunicorn.
- Configure the hosted frontend origin in Django CORS.
- Verify hosted health and trip-plan endpoints plus the four manual acceptance scenarios before recording the Loom.

## Build order

1. Backend foundation and health endpoint
2. Provider clients
3. Pure HOS engine and unit tests
4. Trip API and route progress
5. Daily-log builder and tests
6. Frontend shell and main results
7. SVG logs and printing
8. Full QA, deployment, screenshots, and Loom

Do not begin a later phase while a prerequisite phase’s required tests are failing.