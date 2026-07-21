# Loom Walkthrough — Full Recording Guide

A complete, step-by-step guide to record the 3–5 minute demo: how to set up
Loom, what to have on screen, and **exact word-for-word narration** synced to
what you click.

- **Target length:** 4:00–4:45 (stay under 5:00).
- **Audio:** YES — spoken narration is required. Webcam bubble is optional
  (leave it on; it feels more personal, but off is fine).
- **Everything you need to say is written in quotes below.** Read it naturally;
  you don't have to be word-perfect.

---

## 0. Before you hit record (prep checklist — ~5 min)

Do all of this first so the recording is smooth and you never wait on screen:

1. **Wake the backend** (Render free tier sleeps): open
   `https://hos-route-planner-api.onrender.com/api/health/` in a tab and wait
   for `{"status":"ok"}`. Keep it awake by generating one trip in the app before
   recording, then reload.
2. **Open the live app:** `https://spotter-hos-route-planner.vercel.app` in a
   clean browser window.
   - Close unrelated tabs, bookmarks bar, and notifications (enable Do Not
     Disturb / Focus).
   - Set browser zoom to 100% (Ctrl+0). Use a maximized window.
3. **Pre-run the tests** so you can show green output (optional but strong):
   - Terminal 1: `cd backend && pytest -q` (shows `85 passed`).
   - Terminal 2: `cd frontend && npm test` (shows `18 passed`).
   - Leave both terminals visible, or screenshot the results to show.
4. **Open your code editor (VS Code)** with these files in tabs, in this order,
   so you can click through them quickly:
   - `backend/apps/trips/services/hos_scheduler.py`
   - `backend/apps/trips/services/daily_log_builder.py`
   - `backend/apps/trips/services/routing.py`
   - `frontend/src/features/logs/DailyLogSheet.tsx`
   - `backend/apps/trips/tests/test_hos_scheduler.py`
5. **Rehearse once** with the script below (a single practice run makes the real
   take much cleaner).

---

## 1. How to record with Loom

1. Install **Loom** — the desktop app (recommended, smoother) from
   `https://www.loom.com/download`, or the Chrome extension. Sign in (free plan
   is fine).
2. Click the Loom icon → choose:
   - **Screen + Cam** (or **Screen Only** if you prefer no webcam).
   - **Microphone:** select your mic and **speak a test sentence** to confirm
     the input level is moving. **Do not mute.**
   - **Screen:** "Full screen" (or "Current tab" if you only show the browser —
     but you'll switch to the editor, so pick **Full screen / Desktop**).
3. Click **Start recording** → a 3-2-1 countdown begins.
4. Follow the script in Section 3. Use your mouse to point at what you mention.
5. Press **Stop** (or the Loom shortcut) when done.

---

## 2. Delivery tips

- Speak a little slower than feels natural; pause between sections.
- Move the mouse deliberately to the thing you're describing.
- If you fumble a line, pause 2 seconds and repeat the sentence — you can trim
  it out later in Loom's editor.
- It's fine to glance at this script; just don't read in a monotone.

---

## 3. The script (timed — exact words + on-screen actions)

> Legend: **[DO]** = on-screen action, **[SAY]** = read this aloud.

### 0:00–0:30 — Intro
**[DO]** Show the live app (Vercel URL) at the top, form + header visible.
**[SAY]**
> "Hi — this is my HOS Route Planner, a trip and electronic-log planner for a
> property-carrying truck driver on the 70-hour, 8-day cycle. It's a full-stack
> app: a Django REST API on the backend and a React, TypeScript, and MapLibre
> front end. It plans a route, builds an Hours-of-Service–compliant schedule,
> and generates a daily log sheet for each day. Quick disclaimer up front: this
> is an assessment demo, not a certified ELD."

### 0:30–1:20 — Enter a trip
**[DO]** Click the **Cross-country (B)** sample button. Point at the
"Current cycle used" field.
**[SAY]**
> "I'll load a sample: New York to Pittsburgh for pickup, then out to Los
> Angeles. The key input is 'current cycle used' — that's the on-duty hours the
> driver has already used in their current 70-hour cycle; here it's 10. There's
> also an optional trip-start time so results are reproducible."

**[DO]** Click **Generate trip plan**. While it loads:
**[SAY]**
> "It's calling the Django API now, which geocodes the stops, requests a
> heavy-goods-vehicle route from OpenRouteService, and runs the scheduling
> engine. The API key stays on the server — it never reaches the browser."

### 1:20–2:10 — Route, map, and summary
**[DO]** Point at the summary cards, then the colored count chips, then the map.
**[SAY]**
> "Here's the result. Up top: total distance, the raw driving time versus the
> compliant duration once required stops are added, and the number of log days.
> These chips show the counts — fuel stops, 30-minute breaks, sleeper rests, and
> any 34-hour restarts. On the map you can see the full route with markers for
> the current location, pickup, drop-off, fuel, breaks, and sleeper periods, and
> there's a legend bottom-left."

### 2:10–3:00 — HOS-compliant schedule
**[DO]** Scroll to the timeline. Point at a sleeper card, then a break card.
**[SAY]**
> "This is the chronological schedule, and each stop explains why it was
> scheduled. Here a ten-hour sleeper period is inserted because the driver hit
> the 11-hour driving limit. Here a 30-minute break is required after eight
> cumulative hours of driving. Fuel stops are planned around every 900 miles and
> also satisfy that break. Pickup and drop-off are each 60 minutes, on-duty not
> driving."

**[DO]** In the form, click **Cycle nearly used (C)** → **Generate trip plan**;
scroll to the timeline and point at the 34-hour restart.
**[SAY]**
> "To show the cycle logic — this trip starts with 69 of 70 hours already used,
> so the planner schedules a 34-hour restart before the remaining driving. Which
> leads to an important assumption…"

**[DO]** Expand the **Calculation assumptions** panel briefly.
**[SAY]**
> "The assessment gives one total for cycle hours, not the previous eight days
> individually, so exact recapture can't be computed. I model it conservatively
> as 70 minus hours used, and insert a restart when that's exhausted — and I
> disclose that here in the assumptions panel."

### 3:00–3:40 — Daily log sheets
**[DO]** Scroll to **Driver daily logs**. Click through the day tabs.
**[SAY]**
> "For each calendar day the app generates a log sheet drawn on the standard
> paper-log template. The continuous line is the duty-status graph across 24
> hours, the totals on the right add up to exactly 24 hours, and the remarks
> below list each status change with the time and nearest location. Longer trips
> produce multiple sheets — you can tab between days and print them."

### 3:40–4:30 — Code structure & tests
**[DO]** Switch to VS Code. Click `hos_scheduler.py`, then `daily_log_builder.py`,
then the test file. Show the passing `pytest` / `npm test` output.
**[SAY]**
> "Architecturally, the scheduling engine is a pure, deterministic service —
> here in `hos_scheduler.py` — separate from the API and the HTTP clients, so
> it's fully unit-tested. The daily-log builder splits events at midnight and
> guarantees every day totals 1,440 minutes. There are 85 backend tests covering
> every HOS rule and edge case, and 18 front-end tests — all passing."

### 4:30–5:00 — Wrap-up
**[DO]** Back to the browser; show the footer disclaimer.
**[SAY]**
> "It's deployed — the front end on Vercel, the API on Render — with a complete
> README covering setup, the API, the HOS rules, and the assumptions. Thanks for
> watching."

**[DO]** Stop the recording.

---

## 4. After recording

1. Loom opens the video page automatically. Use **Trim** to cut any dead air at
   the start/end or a fumbled line.
2. Confirm the total is **under 5:00**.
3. Set the video to **"Anyone with the link can view"** (Share → privacy).
4. Copy the share link.
5. Paste the link to me and I'll add it to the README's "Loom walkthrough" spot
   (and it goes into the final cleanup commit).

### Quick fixes if something goes wrong
- **Backend slow / spinner hangs:** the free tier fell asleep — hit
  `/api/health/` once, wait for `ok`, then re-generate. Re-record that segment.
- **CORS or network error in the app:** confirm the backend health URL is `ok`;
  if it persists, tell me and I'll check the Render logs with you.
- **You went over 5 minutes:** cut the Section 3 "Cycle nearly used (C)" detour
  first — the main trip (B) already demonstrates the core features.
