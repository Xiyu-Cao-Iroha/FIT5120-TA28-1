import app.services.route_comparison as route_comparison
from app.config import Settings
from app.services.pedestrian_repository import SegmentPedestrianStats
from app.services.routing_adapter import DemoMelbourneCbdRoutingProvider

ORIGIN = (-37.8183, 144.9671)
DESTINATION = (-37.8095, 144.9646)


class _StubLiveRepo:
    """Stands in for MelbourneOpenDataPedestrianRepository so a test can flip
    live sensor coverage on/off between calls without any real HTTP traffic."""

    coverage_available = True

    def __init__(self, *args, **kwargs):
        pass

    def stats_for_segment(self, polyline, now, sensor_external_id_prefix=None):
        if _StubLiveRepo.coverage_available:
            return SegmentPedestrianStats(sensor_count=1, crowd_score=0.1, has_coverage=True)
        return SegmentPedestrianStats(sensor_count=1, crowd_score=None, has_coverage=False)


def test_live_route_replays_last_known_status_when_coverage_drops(monkeypatch, db_session):
    monkeypatch.setattr(route_comparison, "MelbourneOpenDataPedestrianRepository", _StubLiveRepo)
    route_comparison._LAST_KNOWN_LIVE_STATUS.clear()
    settings = Settings(use_live_melbourne_open_data=True)
    provider = DemoMelbourneCbdRoutingProvider()

    _StubLiveRepo.coverage_available = True
    first = route_comparison.compare_routes(db_session, settings, provider, ORIGIN, DESTINATION)
    assert all(r.sensory_level == "low" for r in first.routes)

    _StubLiveRepo.coverage_available = False
    second = route_comparison.compare_routes(db_session, settings, provider, ORIGIN, DESTINATION)
    assert all(r.sensory_level == "low" for r in second.routes)
    assert all(r.crowd_score == 0.1 for r in second.routes)


def test_live_route_still_unavailable_with_no_prior_cached_status(monkeypatch, db_session):
    monkeypatch.setattr(route_comparison, "MelbourneOpenDataPedestrianRepository", _StubLiveRepo)
    route_comparison._LAST_KNOWN_LIVE_STATUS.clear()
    settings = Settings(use_live_melbourne_open_data=True)
    provider = DemoMelbourneCbdRoutingProvider()

    _StubLiveRepo.coverage_available = False
    result = route_comparison.compare_routes(db_session, settings, provider, ORIGIN, DESTINATION)
    assert all(r.sensory_level == "unavailable" for r in result.routes)
