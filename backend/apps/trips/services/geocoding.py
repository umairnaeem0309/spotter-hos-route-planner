"""
Geocoding and reverse-geocoding via OpenRouteService Pelias.

Called only from Django. The API key is passed as the Pelias ``api_key`` query
parameter by the low-level client; it is never logged (query strings are
stripped) and never returned to the client.

Endpoints:
- search:  {base}/pelias/v1/search
- reverse: {base}/pelias/v1/reverse
"""
from __future__ import annotations

import logging

from apps.trips.types import Coordinate, GeocodedLocation

from .errors import AddressNotFoundError, GeocodingError
from .ors_client import build_url, get_api_key, send

logger = logging.getLogger("apps.trips.geocoding")

_SEARCH_PATH = "pelias/v1/search"
_REVERSE_PATH = "pelias/v1/reverse"


def _first_feature_coordinate(feature: dict) -> Coordinate:
    geometry = feature.get("geometry") or {}
    coords = geometry.get("coordinates")
    if (
        not isinstance(coords, (list, tuple))
        or len(coords) < 2
        or not all(isinstance(c, (int, float)) for c in coords[:2])
    ):
        raise GeocodingError()
    lon, lat = float(coords[0]), float(coords[1])
    return (lon, lat)


def _feature_label(feature: dict, fallback: str) -> str:
    props = feature.get("properties") or {}
    label = props.get("label") or props.get("name")
    return str(label) if label else fallback


def geocode(address: str) -> GeocodedLocation:
    """Resolve a free-text address to a single best-match coordinate/label.

    Raises:
        AddressNotFoundError: the provider returned no usable match (client
            input problem -> HTTP 400).
        GeocodingError / ProviderError: provider/transport failure.
    """
    text = (address or "").strip()
    if not text:
        raise AddressNotFoundError()

    params = {"api_key": get_api_key(), "text": text, "size": 1}
    response = send("GET", build_url(_SEARCH_PATH), params=params)

    if response.status_code >= 400:
        # 4xx that is not 429 (handled in the client): treat as a bad lookup.
        logger.info("Geocoding rejected address (status %s)", response.status_code)
        raise AddressNotFoundError()

    try:
        data = response.json()
    except ValueError as exc:
        raise GeocodingError() from exc

    features = data.get("features") if isinstance(data, dict) else None
    if not features:
        raise AddressNotFoundError()

    feature = features[0]
    coordinate = _first_feature_coordinate(feature)
    label = _feature_label(feature, fallback=text)
    return GeocodedLocation(query=text, label=label, coordinate=coordinate)


def reverse_geocode(coordinate: Coordinate) -> str | None:
    """Return a human label for a coordinate, or ``None`` if unavailable.

    Reverse geocoding is best-effort for labeling generated stops; a failure
    must never abort trip planning, so this returns ``None`` instead of raising
    on a missing match. Transport/transient provider errors still propagate so
    the caller can decide, but callers of generated-stop labeling typically
    guard with a coordinate fallback.
    """
    lon, lat = float(coordinate[0]), float(coordinate[1])
    params = {
        "api_key": get_api_key(),
        "point.lon": lon,
        "point.lat": lat,
        "size": 1,
    }
    response = send("GET", build_url(_REVERSE_PATH), params=params)

    if response.status_code >= 400:
        return None
    try:
        data = response.json()
    except ValueError:
        return None

    features = data.get("features") if isinstance(data, dict) else None
    if not features:
        return None
    return _feature_label(features[0], fallback="")
