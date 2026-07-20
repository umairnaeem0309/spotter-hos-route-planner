# Project Context

## Assessment objective

Build a full-stack Django and React application that accepts:

- Current location
- Pickup location
- Drop-off location
- Current cycle used in hours

It must output:

- Route map
- Route instructions
- Required fuel, rest and sleeper stops
- HOS-compliant trip timeline
- One or more completed driver daily log sheets

## Required deliverables

- GitHub repository
- Hosted frontend
- Hosted backend
- 3–5 minute Loom walkthrough
- Good UI and UX
- Accurate calculations

## Assessment assumptions

- Property-carrying driver
- 70-hour / 8-day cycle
- No adverse driving conditions
- Fuel at least once every 1,000 miles
- Pickup takes one hour
- Drop-off takes one hour

## Primary HOS rules

- Maximum 11 driving hours after a qualifying 10-hour rest
- Driving only within a 14-hour elapsed duty window
- 30-minute non-driving break after 8 cumulative driving hours
- 70 on-duty hours maximum within the modeled cycle
- 10 consecutive hours rest resets daily driving and duty clocks
- 34 consecutive hours off resets the modeled 70-hour cycle

## Important cycle limitation

The assessment only provides total current cycle-used hours. It does not
provide the previous eight individual daily totals.

Therefore exact rolling recapture cannot be calculated.

The application must use a conservative cycle bucket:

available cycle hours = 70 - current cycle used

When the bucket is exhausted and driving remains, schedule a 34-hour restart.

## Reference files

See `docs/references/`.

The FMCSA driver guide is the primary reference for HOS and daily-log
requirements.

The supplied blank log image must be used as the visual base for generated
daily log sheets.