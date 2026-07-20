"""API views for the trips app.

Phase 1 provides only the health check. The trip-planning endpoint is added
in Phase 4; scheduling logic stays out of this layer (ADR-003).
"""
from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    """Liveness probe used by deployments and the frontend warm-up check."""

    def get(self, request: Request) -> Response:
        return Response({"status": "ok"})
