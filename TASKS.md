# Task Tracker

## Phase 0 — Repository setup

- [x] Create GitHub repository
- [x] Create backend and frontend folders
- [x] Add reference files
- [x] Add agent-continuity documents
- [ ] Create initial commit
- [ ] Push initial repository structure

## Phase 1 — Backend foundation

- [ ] Create Django project
- [ ] Install Django REST Framework
- [ ] Configure environment variables
- [ ] Configure CORS
- [ ] Add GET /api/health/
- [ ] Add backend health test
- [ ] Add OpenRouteService client foundation

## Phase 2 — HOS engine

- [ ] Define timeline event types
- [ ] Implement 11-hour limit
- [ ] Implement 14-hour window
- [ ] Implement 30-minute break
- [ ] Implement 70-hour cycle bucket
- [ ] Implement 10-hour sleeper reset
- [ ] Implement 34-hour restart
- [ ] Implement fuel stops
- [ ] Add HOS unit tests

## Phase 3 — Trip API

- [ ] Add trip request serializer
- [ ] Add address geocoding
- [ ] Add current-to-pickup-to-dropoff routing
- [ ] Build trip timeline
- [ ] Add POST /api/trips/plan/
- [ ] Add API integration tests

## Phase 4 — Daily logs

- [ ] Split timeline at midnight
- [ ] Ensure each day totals 24 hours
- [ ] Calculate daily driving miles
- [ ] Build daily-log response model
- [ ] Create SVG overlay
- [ ] Align overlay with supplied template
- [ ] Add print view

## Phase 5 — Frontend

- [ ] Create React Vite TypeScript app
- [ ] Create trip form
- [ ] Create result summary
- [ ] Create MapLibre map
- [ ] Create event timeline
- [ ] Create route instructions
- [ ] Create daily-log viewer
- [ ] Add loading and error states
- [ ] Add responsive styling
- [ ] Add frontend tests

## Phase 6 — Delivery

- [ ] Run backend tests
- [ ] Run frontend tests
- [ ] Run frontend production build
- [ ] Deploy backend
- [ ] Deploy frontend
- [ ] Update README
- [ ] Add screenshots
- [ ] Record Loom
- [ ] Submit links