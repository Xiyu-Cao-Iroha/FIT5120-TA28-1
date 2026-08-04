import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

import app.services.rate_limit as rate_limit_module
from app.db import get_db
from app.main import app
from app.models import PedestrianObservation, PedestrianSensor, Place
from app.services.routing_adapter import DemoMelbourneCbdRoutingProvider

ORIGIN = {"lat": -37.8183, "lon": 144.9671}
DESTINATION = {"lat": -37.8095, "lon": 144.9646}


@pytest.fixture
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    rate_limit_module._limiter = None
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _seed_sensor_and_compare(client, db_session) -> str:
    sensor = PedestrianSensor(
        id=uuid.uuid4(),
        external_id="refuge-test-sensor",
        name="s",
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

    resp = client.post("/api/v1/routes/compare", json={"origin": ORIGIN, "destination": DESTINATION})
    assert resp.status_code == 200
    return resp.json()["routes"][0]["id"]


def _add_place(db_session, name, lat, lon, **meta):
    place = Place(
        id=uuid.uuid4(),
        name=name,
        category="courtyard",
        address="123 Example Street, Melbourne",
        geom=from_shape(Point(lon, lat), srid=4326),
        place_metadata={"data_source": "prototype", **meta},
    )
    db_session.add(place)
    db_session.flush()
    return place


def test_refuges_list_returns_nearby_places(client, db_session):
    route_id = _seed_sensor_and_compare(client, db_session)
    _add_place(db_session, "Nearby Courtyard", -37.8140, 144.9660, short_description="A calm spot.")

    resp = client.get(f"/api/v1/refuges?route_id={route_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["route_id"] == route_id
    assert any(r["name"] == "Nearby Courtyard" for r in body["refuges"])


def test_refuges_list_excludes_far_away_places(client, db_session):
    route_id = _seed_sensor_and_compare(client, db_session)
    _add_place(db_session, "Far Away Place", -37.95, 145.10, short_description="Too far.")

    resp = client.get(f"/api/v1/refuges?route_id={route_id}")
    assert resp.status_code == 200
    names = [r["name"] for r in resp.json()["refuges"]]
    assert "Far Away Place" not in names


def test_refuges_list_empty_is_valid_no_results_state(client, db_session):
    route_id = _seed_sensor_and_compare(client, db_session)
    resp = client.get(f"/api/v1/refuges?route_id={route_id}")
    assert resp.status_code == 200
    assert resp.json()["refuges"] == []


def test_refuges_list_unknown_route_returns_404(client, db_session):
    resp = client.get("/api/v1/refuges?route_id=does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NO_ROUTE_FOUND"


def test_refuge_detail_returns_facility_info(client, db_session):
    route_id = _seed_sensor_and_compare(client, db_session)
    place = _add_place(
        db_session,
        "Nearby Courtyard",
        -37.8140,
        144.9660,
        short_description="A calm spot.",
        facility_info="Seating available.",
        source_note="Prototype location information for demonstration.",
    )

    resp = client.get(f"/api/v1/refuges/{place.id}?route_id={route_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["facility_info"] == "Seating available."
    assert body["data_source"] == "prototype"


def test_refuge_detail_unknown_place_returns_404(client, db_session):
    route_id = _seed_sensor_and_compare(client, db_session)
    resp = client.get(f"/api/v1/refuges/{uuid.uuid4()}?route_id={route_id}")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "REFUGE_NOT_FOUND"


def test_crowd_sensitivity_high_flags_more_routes_as_high(client, db_session):
    """US 1.3 prototype AC: a higher sensitivity preference should make the
    same underlying data more likely to read as High than the default."""
    provider = DemoMelbourneCbdRoutingProvider()
    direct, _alternate = provider.get_candidate_routes((ORIGIN["lat"], ORIGIN["lon"]), (DESTINATION["lat"], DESTINATION["lon"]))

    # Moderate count at every interior point: below the default threshold
    # (0.6) but above a tightened "high sensitivity" threshold (0.6*0.65=0.39).
    for i, (lat, lon) in enumerate(direct.polyline[1:-1], start=1):
        sensor = PedestrianSensor(
            id=uuid.uuid4(),
            external_id=f"sensitivity-test-sensor-{i}",
            name="s",
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
                count=55,  # score ~0.46
                interval_minutes=5,
                quality_flag="ok",
            )
        )
    db_session.flush()

    default_resp = client.post("/api/v1/routes/compare", json={"origin": ORIGIN, "destination": DESTINATION})
    high_resp = client.post(
        "/api/v1/routes/compare",
        json={"origin": ORIGIN, "destination": DESTINATION, "crowd_sensitivity": "high"},
    )
    assert default_resp.status_code == 200
    assert high_resp.status_code == 200

    default_levels = {r["sensory_level"] for r in default_resp.json()["routes"]}
    high_levels = {r["sensory_level"] for r in high_resp.json()["routes"]}
    assert "low" in default_levels
    assert "high" in high_levels
