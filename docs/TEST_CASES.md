# Test Cases

## How to run

```bash
cd backend  && pytest                     # 85 tests
cd frontend && npm test                   # 18 tests
cd frontend && npm run typecheck          # tsc --noEmit
cd frontend && npm run build              # production build
```

## Backend automated tests (pytest, 85)

Provider calls are mocked; no live `ORS_API_KEY` is required.

### HOS engine — `apps/trips/tests/test_hos_scheduler.py`

| # | Case | Expectation |
| --- | --- | --- |
| 1 | < 8 driving hours | no rest break inserted |
| 2 | 9 driving hours | exactly one 30-min break at the 8-hour mark |
| 3 | > 11 driving hours | a 10-hour sleeper inserted; no run exceeds 11 h |
| 4 | 14-hour window | driving stops at the window boundary (white-box) |
| 5 | Fueling | fuel before 1,000 mi, On Duty, resets the break counter |
| 6 | 69 h used | driving stops at 70 h; a 34-hour restart is inserted |
| 6b | 70 h used | restart precedes any driving |
| 7 | Pickup / drop-off | exactly 60 min each, On Duty; pickup satisfies break |
| 10 | Distance | scheduled driving miles reconcile to route distance |
| — | Determinism, integer minutes, tz-aware guard, multi-day validity | invariant checker re-derives all clocks |

### Daily logs — `apps/trips/tests/test_daily_logs.py`

- Every day totals exactly **1,440 minutes**, contiguous, no gaps/overlaps.
- First day is Off Duty until departure.
- Cross-midnight events split across days (both days valid; miles prorated).
- Remarks reference real events (time · location · activity).
- Recap present and bounded; demo metadata flagged; empty input → no logs.

### Trip API — `apps/trips/tests/test_api.py`

- Full response contract returned for a mocked geocode + route.
- Summary values, pickup/drop-off present, daily logs populated.
- No API key/secret leaks into the response.
- Field-level 400s: blank location, cycle out of [0, 70], bad `trip_start`.
- Provider mapping: address-not-found → 400, no-route → 400, unavailable → 502.

### Providers, error schema, config — `test_providers.py`, `test_error_schema.py`, `test_settings.py`, `test_health.py`

- Missing key, timeout, connection error, 429, 5xx, invalid-address, no-route.
- Key-safe URL logging (query stripped).
- Canonical error body; typed errors keep their code; safe 500.
- Production refuses placeholder secret / empty `ALLOWED_HOSTS`; `DEBUG` parsed
  safely; health endpoint returns `{"status":"ok"}`.

## Frontend automated tests (Vitest, 18)

- `TripForm.test.tsx`: blank-field validation, cycle range, sample load + submit,
  server field-error surfacing.
- `TripPlannerPage.test.tsx`: empty state; success render (summary/timeline/
  instructions); API-error state; server validation mapped to fields.
- `logTemplateCoordinates.test.ts`: `minuteToX` endpoints/midpoint/known
  segment/clamping; row order.
- `DailyLogs.test.tsx`: single vs. multi-day, prev/next + tab navigation, SVG
  polyline render.

## Manual acceptance trips (require a live ORS key + both servers)

| ID | Current → Pickup → Drop-off | Cycle | Expected |
| --- | --- | --- | --- |
| A | Chicago, IL → Indianapolis, IN → Nashville, TN | 5 | ~1 log day; 1-h pickup & drop-off; no unnecessary restart |
| B | New York, NY → Pittsburgh, PA → Los Angeles, CA | 10 | multiple log days; multiple 10-h sleepers; breaks; multiple fuel stops |
| C | Chicago, IL → Milwaukee, WI → Dallas, TX | 69 | little cycle left; a 34-h restart before remaining driving; shown on map/timeline/logs |
| D | Any invalid/incomplete address | — | helpful validation/geocoding error; no blank screen; no crash |

Steps: set `ORS_API_KEY` in `backend/.env`, run the backend and frontend, use
the sample buttons (A–C) or type a bad address (D), and verify the expectations.
