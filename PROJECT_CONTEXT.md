# Project Context

## Assessment objective

Build a production-quality demonstration application that accepts a current location, pickup, drop-off, current 70-hour-cycle usage, and optional trip start. It returns a routed trip, a chronological HOS-compliant schedule, operational stops, and one completed driver daily log for each calendar day.

This is a time-boxed assessment, not a certified electronic logging device or legal-compliance product.

## Required deliverables

- Django REST API and React single-page application
- Route map, instructions, summary metrics, event timeline, and daily logs
- Meaningful backend and frontend automated tests
- Hosted frontend and backend
- 3–5 minute Loom walkthrough
- Complete setup, architecture, limitations, testing, and deployment documentation

## Fixed scope

- Property-carrying CMV driver in interstate commerce
- 70-hour/8-day cycle
- Current → pickup → drop-off route
- One-hour pickup and one-hour drop-off, both On Duty, Not Driving
- Fuel planning at 900-mile intervals; each stop lasts 30 minutes
- No adverse-driving, short-haul, personal-conveyance, split-sleeper, or team-driver logic
- No authentication, payments, fleet-management features, or unrelated dashboards

## Core HOS behavior

- Maximum 11 driving hours after a qualifying 10-hour rest
- Driving only inside a 14-consecutive-hour window that begins with the first Driving or On Duty event
- A qualifying 30-minute non-driving period after 8 cumulative driving hours
- Driving prohibited when the modeled 70-hour cycle bucket is exhausted
- Ten consecutive hours Off Duty or Sleeper Berth reset the 11-hour, 14-hour, and break clocks
- A 34-hour restart resets the modeled cycle bucket
- Each calendar-day log must cover exactly 1,440 minutes with no gaps or overlaps

See `docs/HOS_RULES.md` for the implementation contract and source notes.

## Important modeling limitation

The assessment provides total current cycle-used hours, not duty totals for each of the preceding eight days. Exact rolling recapture cannot be calculated. The application therefore uses a conservative cycle bucket:

```text
available cycle hours = 70 - current cycle used
```

If that bucket is exhausted while route driving remains, the planner schedules a 34-consecutive-hour restart. This is an explicit assessment assumption, not a general statement that a restart is legally mandatory.

## Architecture constraints

- Django owns geocoding, routing-provider calls, HOS scheduling, route progress, and daily-log data construction.
- React owns input, map rendering, timeline presentation, log SVG overlays, printing, and user-facing states.
- OpenRouteService credentials never reach the browser.
- Scheduling services must be pure and deterministic when given route data and a fixed trip start.
- The trip-start timezone is used for all generated logs.

See `docs/ARCHITECTURE.md` and `DECISIONS.md`.

## Canonical reference files

- `docs/references/new-full-stack-dev-assessment.docx`
- `docs/references/fmcsa-hos-driver-guide.pdf`
- `docs/references/fmcsa-toc.png`
- `frontend/public/assets/blank-paper-log.png`

The FMCSA guide is an April 2022 guidance document and states that it is not a substitute for the regulations. The blank log image must remain the visual base for generated daily logs.

## Success priorities

1. Correct HOS calculations
2. Correct multi-day log generation
3. Reliable route display and error handling
4. Professional, responsive UI/UX
5. Deployment and a concise demonstration