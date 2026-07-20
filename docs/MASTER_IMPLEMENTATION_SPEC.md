You are a senior full-stack engineer responsible for completing a time-boxed hiring assessment.

Build a production-quality full-stack trip-planning and Hours of Service application using:

- Backend: Django + Django REST Framework
- Frontend: React + Vite + TypeScript
- Styling: Tailwind CSS
- Map renderer: MapLibre GL JS
- Basemap: OpenFreeMap
- Routing/geocoding: HeiGIT/OpenRouteService
- Testing: pytest for Django and Vitest/React Testing Library for React

The final application must be clean, responsive, visually professional, hosted, documented, tested, and suitable for a 3–5 minute demonstration.

Do not only create a plan. Inspect the repository and reference files, implement the application, run it, test it, fix errors, and prepare it for deployment.

==================================================
1. REFERENCE MATERIALS
==================================================

Inspect these files before implementation:

- docs/references/new-full-stack-dev-assessment.docx
- docs/references/fmcsa-hos-driver-guide.pdf
- docs/references/fmcsa-toc.png
- frontend/public/assets/blank-paper-log.png

Also consider this reference video:

https://www.youtube.com/watch?v=whxe41XYXS8

The blank-paper-log.png image must be used as the visual background/template for generated daily log sheets.

Do not replace it with a completely unrelated custom log design.

==================================================
2. ASSESSMENT REQUIREMENTS
==================================================

Create an application that accepts:

1. Current location
2. Pickup location
3. Drop-off location
4. Current cycle used, in hours

Generate:

1. A map displaying:
   - Current-location marker
   - Pickup marker
   - Drop-off marker
   - Complete route
   - Rest-break markers
   - Fuel-stop markers
   - Sleeper-berth markers
   - 34-hour restart marker when required

2. Route information:
   - Total distance
   - Estimated raw driving time
   - Estimated compliant trip duration
   - Estimated arrival time
   - Turn-by-turn route instructions
   - Chronological schedule of driving, pickup, breaks, fueling,
     sleeper periods, restarts, and drop-off

3. Completed driver daily log sheets:
   - Generate one sheet for each calendar day
   - Longer trips must generate multiple sheets
   - Draw the duty-status graph on the supplied blank log template
   - Fill known fields and daily status totals
   - Include remarks for every relevant change of status

Do not add authentication, payments, fleet management, admin dashboards,
or unnecessary features.

==================================================
3. BUSINESS ASSUMPTIONS
==================================================

Implement and clearly display these assumptions:

- Property-carrying commercial motor vehicle driver
- Interstate operation
- 70-hour/8-day cycle
- No adverse-driving-condition exception
- No short-haul exception
- No personal conveyance
- No split sleeper-berth calculations
- No team-driver calculations
- Driver starts the trip after at least ten consecutive hours off duty
- The input "current cycle used" means total on-duty hours already used
  in the driver's current 70-hour cycle
- Because the assessment supplies only one cycle-total value and not the
  previous eight individual days, exact rolling-hour recapture cannot be
  calculated
- Use a conservative cycle-bucket calculation:
  available cycle hours = 70 - current cycle used
- When available cycle hours are exhausted and driving remains, insert
  a 34-consecutive-hour restart
- Assume the truck begins with sufficient fuel
- Schedule fueling before each additional 1,000 route miles
- Use a 900-mile planning interval to avoid exceeding the 1,000-mile
  requirement
- Each fuel stop lasts 30 minutes
- Pickup takes exactly 60 minutes
- Drop-off takes exactly 60 minutes
- Pickup, drop-off, and fueling are On Duty, Not Driving
- A 30-minute fuel event also qualifies as the required non-driving
  break
- Use a ten-hour Sleeper Berth period for overnight daily resets
- Use Off Duty for the 34-hour cycle restart
- Use the trip-start timezone for every generated log, even when the
  route crosses timezones
- Default trip start is the current date and time, but include an
  optional trip-start date/time field so results are reproducible

Show these assumptions in an expandable "Calculation assumptions" panel.

Include a disclaimer that this is an assessment/demo planner and not a
certified ELD or legal-compliance product.

==================================================
4. HOURS OF SERVICE RULES
==================================================

Implement these rules accurately:

A. 11-hour driving limit

The driver may drive no more than 11 total hours following ten
consecutive hours off duty or in the sleeper berth.

B. 14-hour driving window

The driver may drive only during a 14-consecutive-hour window beginning
when the first Driving or On Duty event starts.

The 14-hour clock is based on elapsed wall-clock time.

A normal 30-minute break does not pause or extend this window.

The driver may perform On Duty, Not Driving work after the 14th hour,
but may not drive again until completing ten consecutive hours of
qualifying rest.

C. 30-minute break

After eight cumulative driving hours since the last qualifying
30-minute non-driving period, the driver must take at least 30
consecutive minutes of:

- Off Duty
- Sleeper Berth
- On Duty, Not Driving

Use Off Duty for a normal rest break.

A 30-minute fuel stop can satisfy this requirement.

The trigger concerns cumulative driving time, not eight hours since the
shift started.

D. 70-hour/8-day rule

Driving is prohibited once the driver's modeled cycle total reaches
70 hours.

Count these statuses toward the cycle:

- Driving
- On Duty, Not Driving

Do not count:

- Off Duty
- Sleeper Berth

The driver may remain On Duty, Not Driving beyond 70 hours, but cannot
resume driving until sufficient hours are available.

Because daily history is unavailable, insert a 34-hour restart when the
modeled cycle is exhausted and more driving remains.

E. Ten-hour reset

After ten consecutive hours in Sleeper Berth or Off Duty:

- Reset the 11-hour driving clock
- Reset the 14-hour driving window
- Reset driving time since the most recent qualifying break

It does not reset the 70-hour cycle unless the rest lasts at least 34
consecutive hours.

F. 34-hour restart

After 34 consecutive Off Duty hours:

- Reset modeled cycle-used hours to zero
- Reset the daily 11-hour and 14-hour clocks
- Reset driving-since-break

G. Fueling

Create a fuel event at approximately every 900 route miles.

Fueling is:

- 30 minutes
- On Duty, Not Driving
- Counted toward cycle hours
- A qualifying 30-minute non-driving period

==================================================
5. SCHEDULING ALGORITHM
==================================================

Create a pure, independently testable scheduling engine.

Do not mix scheduling calculations directly into the Django view.

Suggested backend modules:

backend/apps/trips/
├── api/
│   ├── serializers.py
│   ├── urls.py
│   └── views.py
├── services/
│   ├── geocoding.py
│   ├── routing.py
│   ├── hos_scheduler.py
│   ├── route_progress.py
│   └── daily_log_builder.py
├── tests/
│   ├── test_hos_scheduler.py
│   ├── test_daily_logs.py
│   └── test_api.py
└── types.py

Represent every activity as a timeline event:

{
  "type": "driving | pickup | dropoff | fuel | rest_break |
           sleeper_berth | cycle_restart",
  "duty_status": "OFF_DUTY | SLEEPER_BERTH | DRIVING |
                  ON_DUTY_NOT_DRIVING",
  "start_at": "ISO-8601 datetime",
  "end_at": "ISO-8601 datetime",
  "duration_minutes": 60,
  "distance_miles": 0,
  "coordinate": [-87.6298, 41.8781],
  "location_label": "Chicago, IL",
  "description": "Pickup"
}

Planning sequence:

1. Geocode current, pickup, and drop-off addresses.
2. Request a heavy-goods-vehicle route through:
   current -> pickup -> drop-off.
3. Retain route geometry, route segments, steps, distance, and duration.
4. Track how much route time and distance have been consumed.
5. Add driving activity until the earliest upcoming constraint:
   - destination or next operational stop
   - pickup point
   - eight-hour cumulative-driving break
   - eleven-hour driving limit
   - fourteen-hour driving-window limit
   - 70-hour cycle limit
   - 900-mile fuel interval
6. Add the event required by the reached constraint.
7. Continue until drop-off has been completed.
8. Add Off Duty for the remainder of the final calendar day.

Important implementation details:

- Route current location to pickup is driving time and must count toward
  every HOS rule.
- Pickup begins when the route reaches the pickup waypoint.
- Pickup is 60 minutes On Duty, Not Driving.
- Drop-off is 60 minutes On Duty, Not Driving.
- If pickup activity causes the 14-hour window to expire, the driver
  must complete ten hours of rest before further driving.
- If cycle hours reach 70 during pickup, fueling, or another on-duty
  activity, finish that non-driving event but prevent additional driving.
- If a normal break, fuel event, or pickup occurs before eight driving
  hours and lasts at least 30 consecutive minutes, reset the
  driving-since-break counter.
- Do not incorrectly reset the 14-hour window after a 30-minute break.
- Split all activities that cross midnight into separate daily segments.
- Preserve exact internal minute values.
- All generated calendar days must contain exactly 1,440 minutes of
  status activity after Off Duty gaps are filled.

Route-location interpolation:

- Calculate cumulative distance and duration along the returned route.
- Map each scheduled stop to an approximate coordinate on the route.
- Prefer step-level durations and geometry indexes when provided.
- Otherwise interpolate along the LineString using cumulative segment
  distances.
- Reverse geocode generated stop coordinates when practical.
- Fall back to formatted latitude/longitude when reverse geocoding fails.
- Do not claim that a generated fuel coordinate is an actual truck stop
  unless a real POI lookup confirms it.
- Label such stops as "Planned fuel stop along route."

==================================================
6. ROUTING AND GEOCODING
==================================================

All external API requests must be made by Django.

Never expose ORS_API_KEY in frontend code.

Use:

Directions endpoint pattern:

https://api.heigit.org/openrouteservice/v2/directions/driving-hgv/geojson

Geocoding endpoint pattern:

https://api.heigit.org/pelias/v1/search

Reverse-geocoding endpoint pattern:

https://api.heigit.org/pelias/v1/reverse

Use environment variables:

ORS_API_KEY=
DJANGO_SECRET_KEY=
DEBUG=
ALLOWED_HOSTS=
CORS_ALLOWED_ORIGINS=
FRONTEND_URL=

Implement:

- Request timeouts
- Clear exceptions
- Rate-limit error handling
- No-route error handling
- Invalid-address handling
- Missing-key handling
- Appropriate logging
- API responses that do not leak secrets

When displaying the map, use MapLibre with this OpenFreeMap style:

https://tiles.openfreemap.org/styles/liberty

Retain map attribution.

==================================================
7. API CONTRACT
==================================================

Create:

POST /api/trips/plan/

Request:

{
  "current_location": "Chicago, IL",
  "pickup_location": "Indianapolis, IN",
  "dropoff_location": "Dallas, TX",
  "current_cycle_used_hours": 18.5,
  "trip_start": "2026-07-20T08:00:00-05:00"
}

The trip_start property may be omitted.

Validation:

- Locations must not be blank
- current_cycle_used_hours must be between 0 and 70
- trip_start must be valid ISO-8601 when supplied
- Return field-level 400 errors
- Return 502/503 for routing-provider failures with safe messages

Response structure:

{
  "trip_id": "uuid",
  "input": {},
  "summary": {
    "total_distance_miles": 0,
    "raw_driving_minutes": 0,
    "compliant_trip_minutes": 0,
    "departure_at": "",
    "arrival_at": "",
    "number_of_log_days": 0,
    "fuel_stop_count": 0,
    "rest_break_count": 0,
    "overnight_rest_count": 0,
    "cycle_restart_count": 0
  },
  "route": {
    "geometry": {
      "type": "LineString",
      "coordinates": []
    },
    "waypoints": [],
    "instructions": []
  },
  "timeline": [],
  "daily_logs": [],
  "assumptions": [],
  "warnings": []
}

Also create:

GET /api/health/

Return:

{
  "status": "ok"
}

==================================================
8. DAILY LOG GENERATION
==================================================

Use the supplied image:

frontend/public/assets/blank-paper-log.png

Create a reusable React component:

src/features/logs/components/DailyLogSheet.tsx

Use an SVG overlay rather than drawing everything with ordinary
absolutely positioned divs.

Suggested approach:

<svg viewBox="0 0 518 518">
  <image href="/assets/blank-paper-log.png" ... />
  ...generated text and graph lines...
</svg>

Create a coordinate configuration file:

src/features/logs/logTemplateCoordinates.ts

Keep all x/y coordinates in that file.

Do not scatter unexplained pixel numbers throughout the component.

The graph must display these rows:

1. Off Duty
2. Sleeper Berth
3. Driving
4. On Duty, Not Driving

Implement time-to-x conversion:

x = gridStartX +
    (minutesFromMidnight / 1440) * (gridEndX - gridStartX)

Draw:

- Horizontal lines for status durations
- Vertical connectors where status changes
- A continuous polyline for the full 24 hours
- Readable line thickness
- Status totals at the right side
- Remarks beneath the graph

Populate as much known information as possible:

- Date
- From
- To
- Total miles driven that day
- Driver name: "Assessment Driver"
- Carrier: "Spotter Assessment Carrier"
- Main office: "Chicago, IL"
- Truck/trailer: "TRACTOR-001 / TRAILER-001"
- Shipping document: "ASSESSMENT-LOAD"
- Four duty-status totals
- Remarks
- 70-hour recap information that can be calculated from the modeled
  cycle

Make clear in the interface that driver, carrier, vehicle, and shipping
values are demo metadata because the assessment does not collect those
fields.

Remarks should include:

- Time
- Nearest location
- Activity

Examples:

08:00 - Chicago, IL - Began driving
11:30 - Indianapolis, IN - Pickup
12:30 - Indianapolis, IN - Departed pickup
17:00 - Planned fuel stop - Fueling
21:30 - Springfield, MO - Entered sleeper berth

Daily log requirements:

- Each day's status totals must equal exactly 24 hours
- Status lines must start at midnight and end at midnight
- Fill unallocated time as Off Duty
- Split cross-midnight events correctly
- Calculate miles from only that day's driving portions
- Provide previous/next buttons or tabs when multiple logs exist
- Provide a "Print logs" action
- Add print CSS that places one log sheet per printed page
- Add optional PNG/PDF download only after the main functionality is
  stable

Include a development-only coordinate calibration mode for the template.
It may display a temporary coordinate grid while aligning the overlay.
Disable this mode in production.

==================================================
9. FRONTEND USER EXPERIENCE
==================================================

Create a polished single-page application.

Recommended layout:

Header:
- Product name: "HOS Route Planner"
- Small subtitle: "Property-Carrying Driver Trip & ELD Log Planner"

Input section:
- Current location
- Pickup location
- Drop-off location
- Current cycle used
- Optional trip-start date/time
- "Generate trip plan" primary button
- "Load sample trip" secondary button

Results section:
- Summary metric cards
- Interactive route map
- HOS-compliant timeline
- Stops and rests list
- Route instructions accordion
- Daily log-sheet tabs/carousel
- Calculation assumptions
- Warnings/disclaimer

Map marker categories:

- Current location
- Pickup
- Drop-off
- 30-minute rest
- Fuel stop
- Ten-hour sleeper period
- 34-hour restart

Include a visible map legend.

Timeline cards should show:

- Activity icon
- Status
- Start and end time
- Duration
- Location
- Miles driven during the activity
- Explanation of why a stop was scheduled

Examples:

"30-minute rest scheduled because the driver reached eight cumulative
driving hours."

"Ten-hour sleeper period scheduled because the driver reached the
11-hour driving limit."

"34-hour restart scheduled because the modeled 70-hour cycle was
exhausted."

UI quality requirements:

- Responsive on mobile, tablet, and desktop
- Strong visual hierarchy
- Accessible labels
- Keyboard-friendly controls
- Loading skeleton while route is generated
- Empty state before calculation
- Inline form errors
- Helpful API-error state
- No horizontal page overflow
- No raw JSON shown to normal users
- Do not imitate Spotter's logo or use copyrighted branding assets
- A professional navy, teal, white, and neutral visual system is
  acceptable

==================================================
10. FRONTEND STRUCTURE
==================================================

Use a clear feature-based structure:

frontend/src/
├── api/
│   ├── client.ts
│   └── trips.ts
├── components/
│   ├── ui/
│   ├── ErrorState.tsx
│   └── LoadingState.tsx
├── features/
│   ├── trip-form/
│   ├── map/
│   ├── timeline/
│   ├── route-instructions/
│   └── logs/
├── pages/
│   └── TripPlannerPage.tsx
├── types/
│   └── trip.ts
├── App.tsx
└── main.tsx

Use strict TypeScript types matching the Django response.

Use AbortController or equivalent protection against stale requests.

==================================================
11. TESTS
==================================================

Create meaningful automated tests.

Backend unit tests must cover at least:

1. A trip shorter than eight driving hours:
   - No required 30-minute rest break

2. A nine-hour driving trip:
   - One qualifying 30-minute break

3. A trip longer than eleven driving hours:
   - Ten-hour sleeper period inserted
   - No daily driving period exceeds 11 hours

4. Fourteen-hour window:
   - No driving after the 14-hour window expires

5. Fueling:
   - At least one fuel event before the route exceeds 1,000 miles
   - Fuel event is On Duty, Not Driving
   - Fuel event resets driving-since-break

6. Cycle exhaustion:
   - With 69 cycle hours already used, driving is stopped when the
     modeled cycle reaches 70
   - A 34-hour restart is inserted when route driving remains

7. Pickup and drop-off:
   - Exactly 60 minutes each
   - Both counted as On Duty, Not Driving

8. Calendar splitting:
   - Events crossing midnight are split correctly

9. Daily logs:
   - Every log totals exactly 1,440 minutes
   - Generated statuses cover the entire day with no gaps or overlaps

10. Route progression:
   - Distance consumed across activities equals total route distance
     within a small tolerance

Mock external routing/geocoding calls in automated tests.

Create at least one API integration test.

Frontend tests should cover:

- Form validation
- Successful result rendering
- API-error rendering
- Multiple-log navigation
- Correct positioning calculation for a known log segment

Run all tests before declaring completion.

==================================================
12. RELIABILITY AND SECURITY
==================================================

Implement:

- Environment-based configuration
- No committed secrets
- .env.example files
- Django CORS configuration
- Production DEBUG=false behavior
- Secure secret key configuration
- Gunicorn for production
- Consistent API error schema
- Backend request timeout
- Sanitized logs
- Basic throttling if easy, but do not prioritize it over correctness

Do not call the routing API directly from React.

Do not hardcode API keys.

Do not silently invent a route when the provider fails.

A clearly labeled local demo fixture may be included, but it must never
be presented as a live route.

==================================================
13. DEPLOYMENT
==================================================

Prepare a monorepo with:

backend/
frontend/

Frontend deployment:
- Vercel
- Root directory: frontend
- Build command: npm run build
- Output directory: dist
- Environment variable:
  VITE_API_BASE_URL=https://<backend-domain>/api

Backend deployment:
- Prepare for Render or an equivalent Python hosting service
- Root directory: backend
- Build command installs requirements and runs migrations
- Start command uses Gunicorn
- Add render.yaml when practical

Backend production variables:

ORS_API_KEY
DJANGO_SECRET_KEY
DEBUG=false
ALLOWED_HOSTS
CORS_ALLOWED_ORIGINS
FRONTEND_URL

Make sure the frontend production URL is in Django's CORS configuration.

Make sure the deployed frontend can successfully call:

GET /api/health/
POST /api/trips/plan/

Add a warm-up/loading message if the selected backend host may take time
to start.

==================================================
14. README
==================================================

Write a strong root README.md containing:

- Project overview
- Screenshots or screenshot placeholders
- Architecture
- Technology choices
- Local setup
- Backend setup
- Frontend setup
- Environment variables
- API request example
- API response overview
- HOS rules implemented
- Important assumptions
- Explanation of the conservative 70-hour calculation
- Known limitations
- Test commands
- Deployment instructions
- Hosted frontend link placeholder
- Backend API link placeholder
- Loom video link placeholder
- GitHub repository link placeholder

Include this important limitation:

"The assessment provides the total current cycle hours but not the
driver's individual duty totals for the previous eight days. Therefore,
the application cannot calculate exact rolling recapture hours. It uses
the supplied cycle total as a conservative bucket and schedules a
34-hour restart when that bucket is exhausted."

Create:

docs/ARCHITECTURE.md
docs/HOS_RULES.md
docs/LOOM_SCRIPT.md
docs/TEST_CASES.md

==================================================
15. LOOM SCRIPT
==================================================

Create a 3–5 minute Loom script with approximately this timing:

0:00–0:30
- Introduce the application and assignment

0:30–1:20
- Enter a sample trip
- Explain current-cycle input
- Generate the plan

1:20–2:10
- Show route, map markers, rests, fuel stops, and trip summary

2:10–3:00
- Show chronological HOS schedule
- Explain 11-hour, 14-hour, break, sleeper, and cycle logic

3:00–3:40
- Show multiple generated daily log sheets
- Explain duty-status graph and remarks

3:40–4:30
- Show Django service structure, React component structure, and tests

4:30–5:00
- Mention deployment, assumptions, limitations, GitHub, and README

Keep the recorded demonstration below five minutes.

==================================================
16. IMPLEMENTATION ORDER AND TIME BOX
==================================================

Work in this order:

Phase 1: Repository and API foundation
- Inspect reference files
- Create Django and React projects
- Configure environment variables and CORS
- Implement geocoding and routing client

Phase 2: Core HOS engine
- Implement event types and scheduler state
- Implement daily and cycle limits
- Implement breaks, fueling, sleeper rest, and restart
- Write backend unit tests immediately

Phase 3: Daily logs
- Split events by calendar day
- Calculate daily totals and miles
- Implement SVG overlay on the supplied template
- Visually calibrate graph coordinates

Phase 4: User interface
- Form
- Summary
- Map
- Timeline
- Route instructions
- Log navigation
- Loading/error states

Phase 5: Quality and deployment
- Run all tests
- Check responsive layout
- Check at least three trips
- Deploy backend and frontend
- Complete README and Loom script

Prioritize in this order:

1. Correct HOS calculations
2. Correct multi-day log generation
3. Reliable route display
4. Good UI/UX
5. Print/download enhancements
6. Optional extras

Do not spend assessment time on authentication, user accounts, complex
database models, or unrelated fleet-management features.

==================================================
17. MANUAL ACCEPTANCE TESTS
==================================================

Provide a sample-trip button and manually verify:

Test A:
Current: Chicago, IL
Pickup: Indianapolis, IN
Drop-off: Nashville, TN
Cycle used: 5

Expected:
- Likely one log day
- Pickup and drop-off are each one hour
- No unnecessary overnight restart

Test B:
Current: New York, NY
Pickup: Pittsburgh, PA
Drop-off: Los Angeles, CA
Cycle used: 10

Expected:
- Multiple daily logs
- Multiple ten-hour sleeper periods
- 30-minute breaks
- Multiple fuel stops

Test C:
Current: Chicago, IL
Pickup: Milwaukee, WI
Drop-off: Dallas, TX
Cycle used: 69

Expected:
- Very little available cycle driving
- A 34-hour restart before remaining route driving
- Restart displayed on map, timeline, and daily logs

Test D:
Use an invalid or incomplete address.

Expected:
- Helpful validation or geocoding error
- No blank results screen
- No application crash

==================================================
18. DEFINITION OF DONE
==================================================

Do not state that the project is complete until:

- Django API starts successfully
- React application starts successfully
- Production frontend build succeeds
- Backend tests pass
- Frontend tests pass
- Three-location route is displayed
- Pickup and drop-off are included in scheduling
- HOS restrictions are applied
- Fuel stops are applied
- Multiple daily logs are generated for long trips
- Every log totals 24 hours
- Log lines are visually aligned with the supplied template
- No API key appears in browser source or Git history
- README is complete
- Deployment files are present
- No TypeScript errors remain
- No obvious mobile-layout issues remain
- Empty, loading, success, and error states work

==================================================
19. AGENT EXECUTION BEHAVIOR
==================================================

Begin by:

1. Listing the repository contents.
2. Reading the supplied assessment and reference materials.
3. Writing a concise implementation plan.
4. Checking whether any project code already exists.
5. Implementing the project phase by phase.
6. Running formatting, linting, tests, and production builds.
7. Fixing all encountered errors.
8. Reporting:
   - Files created or modified
   - Commands run
   - Tests and build results
   - Environment variables still required
   - Deployment steps remaining
   - Known limitations

Do not pause for clarification unless an essential credential is
missing.

When a requirement is ambiguous, use the assumptions provided in this
prompt, document the decision, and continue.