# Architecture Decisions

## ADR-001: Backend-owned external API calls

Decision:
OpenRouteService requests will be made by Django, not React.

Reason:
The API key must not be exposed in browser source.

## ADR-002: Conservative cycle bucket

Decision:
Use `70 - current_cycle_used` as available cycle time.

Reason:
The assessment does not provide eight days of historical duty totals,
so exact rolling recapture is impossible.

## ADR-003: SVG log overlay

Decision:
Use the supplied blank daily-log image as the SVG background and draw
generated lines and text on top.

Reason:
It preserves the requested paper-log appearance while allowing accurate,
responsive positioning.

## ADR-004: One active owner for HOS scheduling

Decision:
Only one agent or branch may modify the HOS scheduler at a time.

Reason:
The scheduler is the highest-risk part of the project and parallel edits
would create inconsistent rule behavior.