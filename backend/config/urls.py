"""Root URL configuration.

All API routes live under ``/api/``. The trips app owns the health check and
(from Phase 4) the trip-planning endpoint.
"""
from __future__ import annotations

from django.urls import include, path

urlpatterns = [
    path("api/", include("apps.trips.api.urls")),
]
