import uuid
from datetime import datetime, timedelta, timezone

from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from app.models import PedestrianObservation, PedestrianSensor
from app.services.pedestrian_repository import PedestrianDataRepository


def _sensor(db_session, lat, lon, external_id="repo-sensor"):
    sensor = PedestrianSensor(
        id=uuid.uuid4(),
        external_id=external_id,
        name="Repo sensor",
        geom=from_shape(Point(lon, lat), srid=4326),
        active=True,
    )
    db_session.add(sensor)
    db_session.flush()
    return sensor


def test_observation_inside_max_age_is_used(db_session):
    now = datetime.now(timezone.utc)
    sensor = _sensor(db_session, -37.8140, 144.9660)
    db_session.add(
        PedestrianObservation(
            id=uuid.uuid4(),
            sensor_id=sensor.id,
            observed_at=now - timedelta(minutes=29),
            count=50,
            interval_minutes=5,
            quality_flag="ok",
        )
    )
    db_session.flush()

    repo = PedestrianDataRepository(db_session, match_radius_meters=100, max_observation_age_minutes=30)
    stats = repo.stats_for_segment([(-37.8140, 144.9660), (-37.8141, 144.9661)], now)
    assert stats.has_coverage
    assert stats.crowd_score is not None


def test_observation_outside_max_age_is_ignored(db_session):
    now = datetime.now(timezone.utc)
    sensor = _sensor(db_session, -37.8140, 144.9660)
    db_session.add(
        PedestrianObservation(
            id=uuid.uuid4(),
            sensor_id=sensor.id,
            observed_at=now - timedelta(minutes=31),
            count=50,
            interval_minutes=5,
            quality_flag="ok",
        )
    )
    db_session.flush()

    repo = PedestrianDataRepository(db_session, match_radius_meters=100, max_observation_age_minutes=30)
    stats = repo.stats_for_segment([(-37.8140, 144.9660), (-37.8141, 144.9661)], now)
    assert not stats.has_coverage
    assert stats.crowd_score is None


def test_area_with_no_sensor_coverage_is_not_treated_as_low(db_session):
    repo = PedestrianDataRepository(db_session, match_radius_meters=50, max_observation_age_minutes=30)
    stats = repo.stats_for_segment([(-37.9000, 145.1000), (-37.9001, 145.1001)], datetime.now(timezone.utc))
    assert stats.sensor_count == 0
    assert not stats.has_coverage
    assert stats.crowd_score is None
