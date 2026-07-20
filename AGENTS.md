# Agent Instructions

This repository contains a time-boxed Full Stack Developer assessment.

## Mandatory reading order

Before modifying code, read:

1. PROJECT_CONTEXT.md
2. PROJECT_STATUS.md
3. TASKS.md
4. DECISIONS.md
5. HANDOFF.md
6. docs/HOS_RULES.md when available
7. README.md

## Fixed technology stack

- Backend: Django and Django REST Framework
- Frontend: React, Vite and TypeScript
- Map: MapLibre GL JS
- Routing and geocoding: OpenRouteService through Django
- Backend testing: pytest
- Frontend testing: Vitest and React Testing Library

Do not replace the fixed stack without an explicit written instruction.

## Core rules

- Never expose API keys in frontend code.
- Never commit `.env`.
- React must not directly call OpenRouteService.
- HOS scheduling logic must be implemented as pure/testable backend services.
- Do not add authentication, payments or unrelated fleet-management features.
- Do not redesign completed architecture without documenting the reason.
- Work on one TASKS.md item or one clearly defined phase at a time.
- Run relevant tests after every meaningful change.
- Do not claim that work is complete when tests or builds are failing.

## Before ending any session

The agent must:

1. Update PROJECT_STATUS.md.
2. Update TASKS.md checkboxes.
3. Update HANDOFF.md.
4. Record important architecture decisions in DECISIONS.md.
5. Run `git status`.
6. Report modified files, test results, unresolved issues and the exact next task.
7. Commit and push when repository credentials allow it.

## Handoff quality

Never write vague notes such as "continue backend."

The next task must specify:

- Exact file or module
- Expected behavior
- Tests to add or run
- Known blockers
- Acceptance criteria