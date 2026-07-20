# Agent Instructions

This repository contains a time-boxed full-stack developer assessment. Prefer a small, correct, demonstrable implementation over unrelated features.

## Mandatory reading order

Before modifying repository content, read these files completely:

1. `docs/MASTER_IMPLEMENTATION_SPEC.md`
2. `AGENTS.md`
3. `PROJECT_CONTEXT.md`
4. `PROJECT_STATUS.md`
5. `TASKS.md`
6. `DECISIONS.md`
7. `HANDOFF.md`
8. `docs/HOS_RULES.md` when available
9. `README.md`

Before implementation work, also inspect the assessment DOCX, FMCSA guide, FMCSA table-of-contents image, and supplied blank log template listed in `PROJECT_CONTEXT.md`.

## Fixed technology stack

- Backend: Django and Django REST Framework
- Frontend: React, Vite, TypeScript, and Tailwind CSS
- Map: MapLibre GL JS with OpenFreeMap
- Routing and geocoding: OpenRouteService, called only by Django
- Backend testing: pytest
- Frontend testing: Vitest and React Testing Library

Do not replace the fixed stack without an explicit written instruction and an ADR in `DECISIONS.md`.

## Scope and architecture rules

- Never expose API keys in frontend code or API responses.
- Never commit `.env` or credentials. Commit only documented placeholders in `.env.example`.
- React must call the Django API; it must not call OpenRouteService directly.
- Keep HOS scheduling and daily-log construction in pure, deterministic, independently testable backend services.
- Preserve exact internal minute values and timezone-aware datetimes.
- Treat route-provider failures as errors; never silently invent a live route.
- Use the supplied `frontend/public/assets/blank-paper-log.png` as the log-sheet base.
- Do not add authentication, payments, fleet management, admin dashboards, or unrelated features.
- Do not redesign accepted architecture without recording the reason and consequences in `DECISIONS.md`.
- Work on one `TASKS.md` item or one clearly defined phase at a time.
- Run relevant tests after every meaningful change. Do not report completion while required tests or builds fail.

## Change workflow

1. Confirm the current branch, worktree state, and recent commits.
2. Reconcile the requested work with `PROJECT_STATUS.md`, `TASKS.md`, and `HANDOFF.md`.
3. Keep changes within the active phase.
4. Add or update tests with implementation work.
5. Run the narrowest relevant checks first, then the phase-level suite.
6. Review `git diff` and `git status` before handoff.

## Before ending any session

1. Update `PROJECT_STATUS.md` with the date, branch, completed work, tests, blockers, and exact next task.
2. Update `TASKS.md` checkboxes without marking unverified work complete.
3. Update `HANDOFF.md` with concrete commands, results, changed files, and acceptance criteria.
4. Record important architecture decisions in `DECISIONS.md`.
5. Run `git status`.
6. Report modified files, test/build results, unresolved issues, and the exact next task.
7. Commit and push only when requested or when repository credentials and the active workflow clearly allow it.

## Handoff quality

Never write vague notes such as "continue backend." The next task must specify:

- Exact files or modules
- Expected behavior
- Tests to add or run
- Known blockers and required environment variables
- Acceptance criteria