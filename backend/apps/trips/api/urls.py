"""URL routes exposed under ``/api/``."""
from __future__ import annotations

from django.urls import path

from .views import HealthView

app_name = "trips"

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
]
