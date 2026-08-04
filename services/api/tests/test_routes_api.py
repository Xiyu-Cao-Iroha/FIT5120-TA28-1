import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

import app.services.rate_limit as rate_limit_module
from app.config import get_settings
from app.db import get_db
from app.main import app
from app.models import PedestrianObservation, PedestrianSensor
from app.services.geo import point_to_polyline_distance_meters
from app.services.routing_adapter import DemoMelbourneCbdRoutingProvider

ORIGIN = {"lat": -37.8183, "lon": 144.9671}
DESTINATION = {"lat": -37.8095, "lon": 144.9646}

# Comfortably larger than the default sensor_match_radius_meters (75m) so a
# sensor seeded for one demo route can never also match the other route.
MIN_SEPARATION_FROM_OTHER_ROUTE_M = 100.0


@pytest.fixture
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    rate_limit_module._limiter = None  # fresh limiter per test
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _seed_minimal_sensor(db_session):
    sensor = PedestrianSensor(
        id=uuid.uuid4(),
        external_id="api-test-sensor",
        name="Minimal sensor",
        geom=from_shape(Point(144.9660, -37.8140), srid=4326),
        active=True,
    )
    db_session.add(sensor)
    db_session.flush()
    db_session.add(
        PedestrianObservation(
            id=uuid.uuid4(),
            sensor_id=sensor.id,
            observed_at=datetime.now(timezone.utc),
            count=20,
            interval_minutes=5,
            quality_flag="ok",
        )
    )
    db_session.flush()


def _seed_route_corridor(db_session, polyline, count, prefix, other_polyline=None):
    points = polyline[1:-1]
    if other_polyline is not None:
        points = [
            p
            for p in points
            if point_to_polyline_distance_meters(p, other_polyline) >= MIN_SEPARATION_FROM_OTHER_ROUTE_M
        ]
    for i, (lat, lon) in enumerate(points, start=1):
        sensor = PedestrianSensor(
            id=uuid.uuid4(),
            external_id=f"{prefix}-{i}",
            name=prefix,
            geom=from_shape(Point(lon, lat), srid=4326),
            active=True,
        )
        db_session.add(sensor)
        db_session.flush()
        db_session.add(
            PedestrianObservation(
                id=uuid.uuid4(),
                sensor_id=sensor.id,
                observed_at=datetime.now(timezone.utc),
                count=count,
                interval_minutes=5,
                quality_flag="ok",
            )
        )
    db_session.flush()


def test_compare_returns_data_source_unavailable_when_no_sensors_exist(client):
    resp = client.post("/api/v1/routes/compare", json={"origin": ORIGIN, "destination": DESTINATION})
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "DATA_SOURCE_UNAVAILABLE"


def test_compare_returns_routes_when_data_available(client, db_session):
    _seed_minimal_sensor(db_session)
    resp = client.post("/api/v1/routes/compare", json={"origin": ORIGIN, "destination": DESTINATION})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["routes"]) >= 1
    assert body["rule_version"]


def test_identical_origin_and_destination_is_rejected(client, db_session):
    _seed_minimal_sensor(db_session)
    resp = client.post("/api/v1/routes/compare", json={"origin": ORIGIN, "destination": ORIGIN})
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INVALID_LOCATION"


def test_destination_outside_cbd_is_rejected(client, db_session):
    _seed_minimal_sensor(db_session)
    resp = client.post(
        "/api/v1/routes/compare", json={"origin": ORIGIN, "destination": {"lat": -38.5, "lon": 145.5}}
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "OUTSIDE_SERVICE_AREA"


def test_route_detail_not_found_before_any_comparison(client):
    resp = client.get("/api/v1/routes/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NO_ROUTE_FOUND"


def test_route_detail_available_after_comparison(client, db_session):
    _seed_minimal_sensor(db_session)
    compare_resp = client.post("/api/v1/routes/compare", json={"origin": ORIGIN, "destination": DESTINATION})
    route_id = compare_resp.json()["routes"][0]["id"]
    detail_resp = client.get(f"/api/v1/routes/{route_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == route_id


def test_rate_limiting_blocks_after_limit(client, db_session):
    _seed_minimal_sensor(db_session)
    settings = get_settings()
    for _ in range(settings.rate_limit_per_minute):
        resp = client.post("/api/v1/routes/compare", json={"origin": ORIGIN, "destination": DESTINATION})
        assert resp.status_code == 200
    resp = client.post("/api/v1/routes/compare", json={"origin": ORIGIN, "destination": DESTINATION})
    assert resp.status_code == 429
    assert resp.json()["error"]["code"] == "RATE_LIMITED"


def test_recommends_calmer_alternate_over_busier_direct_route(client, db_session):
    provider = DemoMelbourneCbdRoutingProvider()
    direct, alternate = provider.get_candidate_routes(
        (ORIGIN["lat"], ORIGIN["lon"]), (DESTINATION["lat"], DESTINATION["lon"])
    )
    _seed_route_corridor(db_session, direct.polyline, 170, "busy", other_polyline=alternate.polyline)
    _seed_route_corridor(db_session, alternate.polyline, 25, "calm", other_polyline=direct.polyline)

    resp = client.post("/api/v1/routes/compare", json={"origin": ORIGIN, "destination": DESTINATION})
    assert resp.status_code == 200
    routes = {r["id"]: r for r in resp.json()["routes"]}
    assert routes["route-direct"]["sensory_level"] == "high"
    assert routes["route-alternate"]["sensory_level"] == "low"
    assert routes["route-alternate"]["is_recommended"] is True
    assert routes["route-direct"]["is_recommended"] is False


def test_one_route_with_no_data_is_unavailable_and_not_recommended(client, db_session):
    provider = DemoMelbourneCbdRoutingProvider()
    direct, alternate = provider.get_candidate_routes(
        (ORIGIN["lat"], ORIGIN["lon"]), (DESTINATION["lat"], DESTINATION["lon"])
    )
    _seed_route_corridor(db_session, direct.polyline, 25, "calm-direct-only", other_polyline=alternate.polyline)

    resp = client.post("/api/v1/routes/compare", json={"origin": ORIGIN, "destination": DESTINATION})
    assert resp.status_code == 200
    routes = {r["id"]: r for r in resp.json()["routes"]}
    assert routes["route-alternate"]["sensory_level"] == "unavailable"
    assert routes["route-alternate"]["is_recommended"] is False
    assert routes["route-direct"]["is_recommended"] is True


def test_all_routes_congested_end_to_end(client, db_session):
    provider = DemoMelbourneCbdRoutingProvider()
    direct, alternate = provider.get_candidate_routes(
        (ORIGIN["lat"], ORIGIN["lon"]), (DESTINATION["lat"], DESTINATION["lon"])
    )
    _seed_route_corridor(db_session, direct.polyline, 170, "busy1", other_polyline=alternate.polyline)
    _seed_route_corridor(db_session, alternate.polyline, 150, "busy2", other_polyline=direct.polyline)

    resp = client.post("/api/v1/routes/compare", json={"origin": ORIGIN, "destination": DESTINATION})
    assert resp.status_code == 200
    routes = resp.json()["routes"]
    assert all(r["sensory_level"] == "high" for r in routes)
    recommended = [r for r in routes if r["is_recommended"]]
    assert len(recommended) == 1
    assert "not congestion-free" in recommended[0]["explanation"]
