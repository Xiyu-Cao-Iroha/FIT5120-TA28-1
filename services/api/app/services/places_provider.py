import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

GOOGLE_AUTOCOMPLETE_URL = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
GOOGLE_PLACE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

# Bias/restrict Google results to the Melbourne CBD area (requirements
# section 20 decision #1 uses a bounding box for the same purpose; Places
# Autocomplete takes a center point + radius instead).
MELBOURNE_CBD_CENTER = "-37.8136,144.9631"
MELBOURNE_CBD_RADIUS_METERS = 3000


@dataclass(frozen=True)
class PlaceSuggestion:
    place_id: str
    description: str


@dataclass(frozen=True)
class ResolvedPlace:
    place_id: str
    description: str
    lat: float
    lon: float


class PlacesProvider(ABC):
    """Isolates place search behind a stable interface, mirroring the
    RoutingProvider adapter pattern (FR-02), so a production provider can
    replace the demo gazetteer without any client-facing API change."""

    @abstractmethod
    def search(self, query: str) -> list[PlaceSuggestion]:
        raise NotImplementedError

    @abstractmethod
    def resolve(self, place_id: str) -> ResolvedPlace | None:
        raise NotImplementedError


# Mirrors apps/mobile/src/constants/config.ts's CBD_KNOWN_PLACES so the
# fallback experience (no API key configured) stays consistent between
# client and server-side search.
DEMO_GAZETTEER: list[ResolvedPlace] = [
    ResolvedPlace("demo-flinders-street-station", "Flinders Street Station", -37.8183, 144.9671),
    ResolvedPlace("demo-state-library-victoria", "State Library Victoria", -37.8095, 144.9646),
    ResolvedPlace("demo-melbourne-central", "Melbourne Central", -37.8103, 144.9628),
    ResolvedPlace("demo-federation-square", "Federation Square", -37.818, 144.9691),
    ResolvedPlace("demo-queen-victoria-market", "Queen Victoria Market", -37.8076, 144.9568),
]


class DemoGazetteerPlacesProvider(PlacesProvider):
    """Small fixed CBD place list used until a production place-search
    provider is confirmed (requirements section 20 decision #3/#4)."""

    def search(self, query: str) -> list[PlaceSuggestion]:
        normalized = query.strip().lower()
        if not normalized:
            return []
        return [
            PlaceSuggestion(place.place_id, place.description)
            for place in DEMO_GAZETTEER
            if normalized in place.description.lower()
        ]

    def resolve(self, place_id: str) -> ResolvedPlace | None:
        return next((place for place in DEMO_GAZETTEER if place.place_id == place_id), None)


class GooglePlacesProvider(PlacesProvider):
    """FR-01/FR-09 production place search backed by the Google Maps
    Platform Places API. Only used when GOOGLE_MAPS_API_KEY is configured."""

    def __init__(self, api_key: str, timeout_seconds: float = 8.0):
        self._api_key = api_key
        self._timeout = timeout_seconds

    def search(self, query: str) -> list[PlaceSuggestion]:
        if not query.strip():
            return []
        params = {
            "input": query,
            "location": MELBOURNE_CBD_CENTER,
            "radius": MELBOURNE_CBD_RADIUS_METERS,
            "strictbounds": "true",
            "components": "country:au",
            "key": self._api_key,
        }
        try:
            response = httpx.get(GOOGLE_AUTOCOMPLETE_URL, params=params, timeout=self._timeout)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError:
            logger.exception("Google Places Autocomplete request failed")
            return []

        if payload.get("status") not in ("OK", "ZERO_RESULTS"):
            logger.warning("Google Places Autocomplete returned status=%s", payload.get("status"))
            return []

        return [
            PlaceSuggestion(place_id=p["place_id"], description=p["description"])
            for p in payload.get("predictions", [])
            if "place_id" in p and "description" in p
        ]

    def resolve(self, place_id: str) -> ResolvedPlace | None:
        params = {"place_id": place_id, "fields": "geometry,formatted_address", "key": self._api_key}
        try:
            response = httpx.get(GOOGLE_PLACE_DETAILS_URL, params=params, timeout=self._timeout)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError:
            logger.exception("Google Place Details request failed")
            return None

        if payload.get("status") != "OK":
            logger.warning("Google Place Details returned status=%s", payload.get("status"))
            return None

        result = payload.get("result", {})
        location = result.get("geometry", {}).get("location")
        if not location:
            return None

        return ResolvedPlace(
            place_id=place_id,
            description=result.get("formatted_address", ""),
            lat=location["lat"],
            lon=location["lng"],
        )


def get_places_provider(api_key: str | None, timeout_seconds: float = 8.0) -> PlacesProvider:
    if api_key:
        return GooglePlacesProvider(api_key, timeout_seconds)
    return DemoGazetteerPlacesProvider()
