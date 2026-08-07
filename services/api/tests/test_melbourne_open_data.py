from datetime import datetime, timedelta, timezone

import httpx

from app.services.melbourne_open_data import MelbourneOpenDataPedestrianRepository

CBD_BOUNDS = (-37.8230, -37.8050, 144.9400, 144.9700)


class _FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=None, response=self)

    def json(self) -> dict:
        return self._payload


def test_matched_sensor_with_recent_counts_scores_the_segment(monkeypatch):
    now = datetime.now(timezone.utc)

    def fake_get(url, params=None, timeout=None):
        if "sensor-locations" in url:
            return _FakeResponse({"results": [{"location_id": 4, "latitude": -37.8140, "longitude": 144.9660}]})
        recent = (now - timedelta(minutes=2)).isoformat()
        return _FakeResponse({"results": [{"location_id": 4, "sensing_datetime": recent, "total_of_directions": 30}]})

    monkeypatch.setattr(httpx, "get", fake_get)

    repo = MelbourneOpenDataPedestrianRepository(
        match_radius_meters=100, max_observation_age_minutes=30, cbd_bounds=CBD_BOUNDS
    )
    stats = repo.stats_for_segment([(-37.8140, 144.9660), (-37.8141, 144.9661)], now)

    assert stats.has_coverage
    assert stats.sensor_count == 1
    # 30 pedestrians/min * 5 (normalised to the 5-min reference window) / 120 reference capacity
    assert stats.crowd_score == 1.0


def test_stale_counts_are_excluded(monkeypatch):
    now = datetime.now(timezone.utc)

    def fake_get(url, params=None, timeout=None):
        if "sensor-locations" in url:
            return _FakeResponse({"results": [{"location_id": 4, "latitude": -37.8140, "longitude": 144.9660}]})
        stale = (now - timedelta(minutes=45)).isoformat()
        return _FakeResponse({"results": [{"location_id": 4, "sensing_datetime": stale, "total_of_directions": 30}]})

    monkeypatch.setattr(httpx, "get", fake_get)

    repo = MelbourneOpenDataPedestrianRepository(
        match_radius_meters=100, max_observation_age_minutes=30, cbd_bounds=CBD_BOUNDS
    )
    stats = repo.stats_for_segment([(-37.8140, 144.9660), (-37.8141, 144.9661)], now)

    assert stats.sensor_count == 1
    assert not stats.has_coverage
    assert stats.crowd_score is None


def test_no_nearby_sensor_returns_no_coverage(monkeypatch):
    now = datetime.now(timezone.utc)

    def fake_get(url, params=None, timeout=None):
        if "sensor-locations" in url:
            return _FakeResponse({"results": [{"location_id": 4, "latitude": -37.8140, "longitude": 144.9660}]})
        return _FakeResponse({"results": []})

    monkeypatch.setattr(httpx, "get", fake_get)

    repo = MelbourneOpenDataPedestrianRepository(
        match_radius_meters=50, max_observation_age_minutes=30, cbd_bounds=CBD_BOUNDS
    )
    stats = repo.stats_for_segment([(-37.9000, 145.1000), (-37.9001, 145.1001)], now)

    assert stats.sensor_count == 0
    assert not stats.has_coverage
    assert stats.crowd_score is None


def test_sensors_are_fetched_only_once_per_instance(monkeypatch):
    now = datetime.now(timezone.utc)
    call_count = {"sensor_locations": 0}

    def fake_get(url, params=None, timeout=None):
        if "sensor-locations" in url:
            call_count["sensor_locations"] += 1
            return _FakeResponse({"results": [{"location_id": 4, "latitude": -37.8140, "longitude": 144.9660}]})
        return _FakeResponse({"results": []})

    monkeypatch.setattr(httpx, "get", fake_get)

    repo = MelbourneOpenDataPedestrianRepository(
        match_radius_meters=100, max_observation_age_minutes=30, cbd_bounds=CBD_BOUNDS
    )
    repo.stats_for_segment([(-37.8140, 144.9660), (-37.8141, 144.9661)], now)
    repo.stats_for_segment([(-37.8140, 144.9660), (-37.8141, 144.9661)], now)

    assert call_count["sensor_locations"] == 1


def test_network_failure_returns_no_coverage_instead_of_raising(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        raise httpx.ConnectError("boom")

    monkeypatch.setattr(httpx, "get", fake_get)

    repo = MelbourneOpenDataPedestrianRepository(
        match_radius_meters=100, max_observation_age_minutes=30, cbd_bounds=CBD_BOUNDS
    )
    stats = repo.stats_for_segment(
        [(-37.8140, 144.9660), (-37.8141, 144.9661)], datetime.now(timezone.utc)
    )

    assert stats.sensor_count == 0
    assert not stats.has_coverage
    assert stats.crowd_score is None
