# Task Tracker

Only mark an item complete after its acceptance checks pass.

## Phase 0 — Repository and documentation foundation

- [x] Capture Git status, branch, and recent history
- [x] Read the master specification and continuity documents
- [x] Inspect the assessment DOCX, FMCSA PDF/TOC, and blank log asset
- [x] Normalize required reference filenames
- [x] Document scope, architecture, HOS rules, security, and environment variables
- [x] Update status, decisions, handoff, README, and agent instructions
- [x] Review, commit, and push the documentation foundation

## Phase 1 — Backend foundation

- [x] Create the Django project and `apps/trips/` package under `backend/`
- [x] Add Django REST Framework, pytest, pytest-django, and django-cors-headers
- [x] Configure environment-based development and production settings
- [x] Configure CORS from `CORS_ALLOWED_ORIGINS` and `FRONTEND_URL`
- [x] Add `GET /api/health/`
- [x] Add health/configuration tests and run pytest

## Phase 2 — Routing provider foundation

- [x] Define typed provider errors and a consistent safe API error schema
- [x] Implement backend-only OpenRouteService geocoding/reverse-geocoding clients
- [x] Implement `driving-hgv` routing through current → pickup → drop-off
- [x] Add timeouts, missing-key, invalid-address, no-route, and rate-limit handling
- [x] Add mocked provider tests; never require a live API key in automated tests

## Phase 3 — Pure HOS engine

- [x] Define timeline event and scheduler-state types
- [x] Implement pickup/drop-off events and route consumption
- [x] Implement the 11-hour driving limit and 10-hour reset
- [x] Implement the elapsed 14-hour driving window
- [x] Implement the cumulative 8-hour/30-minute break rule
- [x] Implement the conservative 70-hour cycle bucket and 34-hour restart
- [x] Implement 900-mile fuel planning and qualifying-break behavior
- [x] Add unit tests for every required edge case in the master specification

## Phase 4 — Trip API and route progress

- [x] Add request serializer and field-level validation
- [x] Map scheduled progress to approximate route coordinates
- [x] Add safe reverse-geocode fallback labels
- [x] Implement `POST /api/trips/plan/` response contract
- [x] Add mocked API integration tests and distance-tolerance tests

## Phase 5 — Daily-log backend

- [x] Split events at midnight using the trip-start timezone
- [x] Fill gaps with Off Duty and enforce exactly 1,440 minutes per day
- [x] Calculate daily status totals, driving miles, remarks, and modeled recap
- [x] Add daily-log tests for gaps, overlaps, cross-midnight events, and totals

## Phase 6 — Frontend foundation and features

- [ ] Create the React/Vite/TypeScript/Tailwind application under `frontend/`
- [ ] Add strict API types and a stale-request-safe client
- [ ] Build the trip form, validation, empty/loading/error states, and sample trip
- [ ] Build summary cards, MapLibre/OpenFreeMap route map, markers, and legend
- [ ] Build timeline, stops, assumptions, warnings, and instructions UI
- [ ] Add accessible, responsive behavior and frontend tests

## Phase 7 — Daily-log UI

- [ ] Create centralized template coordinate configuration
- [ ] Overlay a continuous SVG status graph on `blank-paper-log.png`
- [ ] Render fields, status totals, remarks, and demo metadata disclosure
- [ ] Add multi-log navigation, development calibration mode, and print CSS
- [ ] Add position-calculation and navigation tests

## Phase 8 — Quality and delivery

- [ ] Run all backend tests
- [ ] Run frontend tests, type checking, linting, and production build
- [ ] Complete manual acceptance trips A–D
- [ ] Verify no secret appears in tracked files or browser code
- [ ] Add deployment configuration and deploy backend/frontend
- [ ] Add screenshots, final links, test cases, and Loom script
- [ ] Record a 3–5 minute Loom walkthrough