import httpx
import pytest

from app.services.places_provider import (
    DemoGazetteerPlacesProvider,
    GooglePlacesProvider,
    PlaceSuggestion,
    get_places_provider,
)
from app.services.routing_adapter import (
    DemoMelbourneCbdRoutingProvider,
    GoogleDirectionsRoutingProvider,
    get_routing_provider,
)


class _FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=None, response=self)

    def json(self) -> dict:
        return self._payload


# Known-good encoded polyline from Google's own algorithm documentation
# (decodes to 3 points) - only used to check parsing plumbing here, not
# geographic accuracy (see test_polyline.py for that).
_FAKE_ENCODED_POLYLINE = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"


def test_get_routing_provider_falls_back_to_demo_without_api_key():
    # get_routing_provider always wraps the selected provider in
    # CachedSnapshotRoutingProvider (see routing_adapter.py) so pinned demo
    # pairs stay repeatable; check the wrapped provider underneath.
    assert isinstance(get_routing_provider(None).inner, DemoMelbourneCbdRoutingProvider)
    assert isinstance(get_routing_provider("").inner, DemoMelbourneCbdRoutingProvider)


def test_get_routing_provider_uses_google_with_api_key():
    assert isinstance(get_routing_provider("fake-key").inner, GoogleDirectionsRoutingProvider)


def test_google_directions_parses_routes(monkeypatch):
    payload = {
        "status": "OK",
        "routes": [
            {
                "summary": "Collins St",
                "overview_polyline": {"points": _FAKE_ENCODED_POLYLINE},
                "legs": [{"duration": {"value": 600}, "distance": {"value": 800}}],
            }
        ],
    }

    def fake_get(url, params=None, timeout=None):
        assert "directions" in url
        return _FakeResponse(payload)

    monkeypatch.setattr(httpx, "get", fake_get)

    provider = GoogleDirectionsRoutingProvider("fake-key")
    routes = provider.get_candidate_routes((-37.8183, 144.9671), (-37.8095, 144.9646))

    assert len(routes) == 1
    assert routes[0].name == "Route via Collins St"
    assert routes[0].duration_minutes == 10.0
    assert routes[0].distance_meters == 800.0
    assert len(routes[0].segments) >= 1


def test_google_directions_returns_empty_on_non_ok_status(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        return _FakeResponse({"status": "ZERO_RESULTS", "routes": []})

    monkeypatch.setattr(httpx, "get", fake_get)

    provider = GoogleDirectionsRoutingProvider("fake-key")
    routes = provider.get_candidate_routes((-37.8183, 144.9671), (-37.8095, 144.9646))
    assert routes == []


def test_google_directions_returns_empty_on_network_error(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        raise httpx.ConnectError("boom")

    monkeypatch.setattr(httpx, "get", fake_get)

    provider = GoogleDirectionsRoutingProvider("fake-key")
    routes = provider.get_candidate_routes((-37.8183, 144.9671), (-37.8095, 144.9646))
    assert routes == []


def test_get_places_provider_falls_back_to_gazetteer_without_api_key():
    assert isinstance(get_places_provider(None), DemoGazetteerPlacesProvider)


def test_demo_gazetteer_search_and_resolve():
    provider = DemoGazetteerPlacesProvider()
    results = provider.search("state library")
    assert len(results) == 1
    assert results[0].description == "State Library Victoria"

    resolved = provider.resolve(results[0].place_id)
    assert resolved is not None
    assert resolved.lat == pytest.approx(-37.8095)


def test_google_places_search_parses_predictions(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        assert "autocomplete" in url
        return _FakeResponse(
            {
                "status": "OK",
                "predictions": [{"place_id": "abc123", "description": "State Library Victoria, Melbourne VIC"}],
            }
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    provider = GooglePlacesProvider("fake-key")
    results = provider.search("state library")
    assert results == [PlaceSuggestion("abc123", "State Library Victoria, Melbourne VIC")]


def test_google_places_resolve_parses_geometry(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        assert "details" in url
        return _FakeResponse(
            {
                "status": "OK",
                "result": {
                    "formatted_address": "328 Swanston St, Melbourne VIC 3000",
                    "geometry": {"location": {"lat": -37.8095, "lng": 144.9646}},
                },
            }
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    provider = GooglePlacesProvider("fake-key")
    resolved = provider.resolve("abc123")
    assert resolved is not None
    assert resolved.lat == -37.8095
    assert resolved.lon == 144.9646
    assert resolved.description == "328 Swanston St, Melbourne VIC 3000"
