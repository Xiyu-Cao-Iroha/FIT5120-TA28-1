import uuid
from datetime import datetime, timezone

import pytest
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy.exc import IntegrityError

from app.models import PedestrianObservation, PedestrianSensor


def _sensor(db_session, external_id="s-constraint"):
    sensor = PedestrianSensor(
        id=uuid.uuid4(),
        external_id=external_id,
        name="Test sensor",
        geom=from_shape(Point(144.96, -37.81), srid=4326),
        active=True,
    )
    db_session.add(sensor)
    db_session.flush()
    return sensor


def test_negative_count_is_rejected(db_session):
    sensor = _sensor(db_session)
    db_session.add(
        PedestrianObservation(
            id=uuid.uuid4(),
            sensor_id=sensor.id,
            observed_at=datetime.now(timezone.utc),
            count=-1,
            interval_minutes=5,
            quality_flag="ok",
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_duplicate_sensor_and_timestamp_is_rejected(db_session):
    sensor = _sensor(db_session)
    ts = datetime.now(timezone.utc)
    db_session.add(
        PedestrianObservation(
            id=uuid.uuid4(), sensor_id=sensor.id, observed_at=ts, count=10, interval_minutes=5, quality_flag="ok"
        )
    )
    db_session.flush()
    db_session.add(
        PedestrianObservation(
            id=uuid.uuid4(), sensor_id=sensor.id, observed_at=ts, count=20, interval_minutes=5, quality_flag="ok"
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_zero_count_is_accepted(db_session):
    sensor = _sensor(db_session)
    db_session.add(
        PedestrianObservation(
            id=uuid.uuid4(),
            sensor_id=sensor.id,
            observed_at=datetime.now(timezone.utc),
            count=0,
            interval_minutes=5,
            quality_flag="ok",
        )
    )
    db_session.flush()  # should not raise
