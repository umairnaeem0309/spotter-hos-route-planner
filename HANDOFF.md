# Latest Handoff

Date:
Agent:
Branch:
Latest commit:

## Work completed this session

- None yet

## Files changed

- None yet

## Commands run

- None yet

## Test results

- No tests run yet

## Current working behavior

- Repository structure only

## Broken or incomplete behavior

- Application has not been initialized

## Important decisions

- See DECISIONS.md

## Environment variables required

- ORS_API_KEY
- DJANGO_SECRET_KEY
- DEBUG
- ALLOWED_HOSTS
- CORS_ALLOWED_ORIGINS
- VITE_API_BASE_URL

## Exact next task

Create the Django backend foundation and `/api/health/`.

## Acceptance criteria for next task

- Django development server starts
- GET `/api/health/` returns `{"status": "ok"}`
- A pytest test verifies the endpoint
- No secret is committed