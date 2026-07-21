# Loom Walkthrough Script (3–5 minutes)

Keep the recording under 5 minutes. Have the app open with the backend awake
(hit `/api/health/` once first so the free-tier backend is warm).

## 0:00–0:30 — Intro

- "This is the HOS Route Planner — a trip and ELD daily-log planner for a
  property-carrying driver on the 70-hour / 8-day cycle."
- "The backend is Django + DRF; the frontend is React, Vite, TypeScript, and
  MapLibre. It's an assessment demo, not a certified ELD."

## 0:30–1:20 — Enter a trip

- Click **Load sample** → "Cross-country (B)" (New York → Pittsburgh → LA).
- Point out the **current cycle used** field: "This is total on-duty hours
  already used in the current 70-hour cycle."
- Mention the optional trip-start for reproducible results.
- Click **Generate trip plan**; note the loading skeleton / warm-up message.

## 1:20–2:10 — Route, map, summary

- Walk the **summary cards**: total distance, raw vs. compliant duration,
  arrival, and the stop counts (fuel / breaks / sleepers / restarts).
- On the **map**: point out the current/pickup/drop-off markers, the route line,
  and the fuel/break/sleeper markers with the **legend**.

## 2:10–3:00 — HOS schedule

- Scroll the **timeline**. Pick a few cards and read the reason text:
  - "Ten-hour sleeper period because the driver reached the 11-hour limit."
  - "30-minute rest because the driver reached eight cumulative driving hours."
  - "Fuel stop at the ~900-mile interval, which also satisfies the break."
- If showing trip C, highlight the **34-hour restart** ("modeled 70-hour cycle
  exhausted").

## 3:00–3:40 — Daily logs

- Open **Driver daily logs**; switch between **Day 1 / Day 2 …** tabs.
- Point at the continuous **duty-status graph** on the blank log template, the
  right-hand **status totals**, and the **remarks** (time · location · activity).
- Note the demo-metadata disclosure and the **Print logs** button (one sheet per
  page).

## 3:40–4:30 — Code structure & tests

- Backend: `services/` — `hos_scheduler.py` (pure engine), `daily_log_builder.py`,
  `routing.py`/`geocoding.py`; "the API key is server-side only."
- Tests: `cd backend && pytest` (85 passing); `cd frontend && npm test`
  (18 passing).

## 4:30–5:00 — Wrap-up

- Deployment: Render (backend) + Vercel (frontend).
- Assumptions & limitations: the **Calculation assumptions** panel and the
  conservative 70-hour bucket.
- Mention the GitHub repo and README. Done.
