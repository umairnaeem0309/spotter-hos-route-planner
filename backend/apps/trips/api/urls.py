"""URL routes exposed under ``/api/``."""
from __future__ import annotations

from django.urls import path

from .views import HealthView, TripPlanView

app_name = "trips"

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("trips/plan/", TripPlanView.as_view(), name="trip-plan"),
]
