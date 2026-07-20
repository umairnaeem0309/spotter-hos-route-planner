"""Tests for the health endpoint and the canonical error schema."""
from __future__ import annotations

import pytest
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture()
def client() -> APIClient:
    return APIClient()


def test_health_returns_ok(client: APIClient) -> None:
    response = client.get("/api/health/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}


def test_health_is_json(client: APIClient) -> None:
    response = client.get("/api/health/")

    assert response["Content-Type"].startswith("application/json")


def test_unknown_route_returns_404(client: APIClient) -> None:
    response = client.get("/api/does-not-exist/")

    assert response.status_code == status.HTTP_404_NOT_FOUND
