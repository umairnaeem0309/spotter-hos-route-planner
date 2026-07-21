# Architecture Decisions

## ADR-001: Fixed monorepo stack

**Status:** Accepted

**Decision:** Use Django + Django REST Framework in `backend/` and React + Vite + TypeScript + Tailwind CSS in `frontend/`. Use pytest for backend tests and Vitest/React Testing Library for frontend tests.

**Reason:** This is the assessment’s required stack and provides clear backend/frontend deployment boundaries.

## ADR-002: Backend-owned routing and geocoding

**Status:** Accepted

**Decision:** Django is the only component allowed to call OpenRouteService. React calls the Django API and receives provider-neutral route data.

**Reason:** The OpenRouteService API key must never be exposed in browser code, logs, or responses.

## ADR-003: Pure deterministic scheduling core

**Status:** Accepted

**Decision:** HOS scheduling, route progress, and daily-log construction live in pure/testable backend service modules, separate from serializers, views, HTTP clients, and persistence.

**Reason:** HOS edge cases are the highest-risk requirement. Deterministic services allow focused unit testing without network or Django request state.

## ADR-004: Conservative cycle bucket

**Status:** Accepted

**Decision:** Model available cycle time as `70 - current_cycle_used_hours`. Count Driving and On Duty, Not Driving against the bucket. Insert a 34-hour restart when the bucket prevents further required driving.

**Reason:** The assessment omits the preceding eight individual daily totals, so exact rolling recapture cannot be calculated. The UI and API must disclose this limitation.

## ADR-005: Simplified sleeper and restart statuses

**Status:** Accepted

**Decision:** Use a 10-hour Sleeper Berth event for overnight resets and an Off Duty event for the modeled 34-hour restart. Do not implement split-sleeper or team-driver pairing.

**Reason:** This matches the assessment assumptions while keeping the scheduler auditable and bounded.

## ADR-006: Single trip timezone

**Status:** Accepted

**Decision:** Use the trip-start timezone for the entire schedule and every generated log, including routes crossing timezones.

**Reason:** A consistent time base is required for reproducible calendar splitting. It approximates the FMCSA home-terminal time-base requirement because the assessment does not collect a home terminal.

## ADR-007: Route progress and generated-stop labels

**Status:** Accepted

**Decision:** Retain route geometry, segments, steps, distance, and duration. Map event progress to route coordinates using step detail when available and distance interpolation otherwise. Label generated fuel locations as planned points along the route unless a real POI source confirms a truck stop.

**Reason:** Scheduled stops need defensible map positions without inventing businesses or facilities.

## ADR-008: SVG overlay on the supplied log image

**Status:** Accepted

**Decision:** Use `frontend/public/assets/blank-paper-log.png` as an SVG `<image>` background. Store overlay coordinates centrally and draw a continuous 24-hour polyline plus field text and remarks.

**Reason:** This preserves the supplied paper-log design while supporting scalable and testable time-to-position calculations.

## ADR-009: Stateless initial trip planning

**Status:** Accepted

**Decision:** The initial `POST /api/trips/plan/` implementation will calculate and return a plan without requiring a database-backed trip model. A response UUID may identify the calculation.

**Reason:** Persistence is not required by the assessment and would consume time without improving the core demonstration.