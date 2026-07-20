"""API views for the trips app.

Views stay thin: they validate input, delegate to the service layer, and let
the safe exception handler render typed errors. No scheduling or provider logic
lives here (ADR-003).
"""
from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.trips.services.trip_planner import build_trip_plan

from .serializers import TripPlanRequestSerializer


class HealthView(APIView):
    """Liveness probe used by deployments and the frontend warm-up check."""

    def get(self, request: Request) -> Response:
        return Response({"status": "ok"})


class TripPlanView(APIView):
    """POST /api/trips/plan/ — validate input and return a full trip plan."""

    def post(self, request: Request) -> Response:
        serializer = TripPlanRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        plan = build_trip_plan(
            current_location=data["current_location"],
            pickup_location=data["pickup_location"],
            dropoff_location=data["dropoff_location"],
            current_cycle_used_hours=data["current_cycle_used_hours"],
            trip_start=data.get("trip_start"),
        )
        return Response(plan)
