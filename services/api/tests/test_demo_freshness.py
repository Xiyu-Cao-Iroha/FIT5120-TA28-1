import uuid
from datetime import datetime, timedelta, timezone

from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from app.models import PedestrianObservation, PedestrianSensor
from app.seed import refresh_demo_scenario_freshness

STALE_AGE = timedelta(hours=3)


def _add_sensor_with_observations(db_session, external_id, stagger_minutes=(0, 5, 10)):
    now = datetime.now(timezone.utc) - STALE_AGE
    sensor = PedestrianSensor(
        id=uuid.uuid4(),
        external_id=external_id,
        name=external_id,
        geom=from_shape(Point(144.9631, -37.8136), srid=4326),
        active=True,
    )
    db_session.add(sensor)
    db_session.flush()
    for minutes in stagger_minutes:
        db_session.add(
            PedestrianObservation(
                id=uuid.uuid4(),
                sensor_id=sensor.id,
                observed_at=now - timedelta(minutes=minutes),
                count=100,
                interval_minutes=5,
                quality_flag="ok",
            )
        )
    db_session.flush()
    return sensor


def test_refresh_shifts_stale_demo_observations_to_fresh(db_session):
    demo_sensor = _add_sensor_with_observations(db_session, "demo-contrast-r0-1")
    real_sensor = _add_sensor_with_observations(db_session, "api-test-sensor")

    updated = refresh_demo_scenario_freshness(db_session)
    assert updated == 3

    demo_observations = (
        db_session.query(PedestrianObservation)
        .filter(PedestrianObservation.sensor_id == demo_sensor.id)
        .order_by(PedestrianObservation.observed_at.desc())
        .all()
    )
    now = datetime.now(timezone.utc)
    assert (now - demo_observations[0].observed_at) < timedelta(minutes=1)
    # Relative staggering between a sensor's own observations is preserved,
    # not collapsed onto one identical timestamp (would violate the
    # (sensor_id, observed_at) unique constraint).
    assert (demo_observations[0].observed_at - demo_observations[1].observed_at) == timedelta(minutes=5)
    assert (demo_observations[1].observed_at - demo_observations[2].observed_at) == timedelta(minutes=5)

    real_observations = (
        db_session.query(PedestrianObservation).filter(PedestrianObservation.sensor_id == real_sensor.id).all()
    )
    assert all((now - o.observed_at) >= STALE_AGE - timedelta(minutes=1) for o in real_observations)


def test_refresh_is_safe_to_call_repeatedly(db_session):
    # Real time always advances between two calls, so a second call still
    # nudges observed_at forward slightly rather than returning exactly 0 -
    # what matters is that calling it back-to-back doesn't error (e.g. by
    # colliding with the unique constraint) and observations stay fresh.
    demo_sensor = _add_sensor_with_observations(db_session, "demo-contrast-r0-1")
    refresh_demo_scenario_freshness(db_session)
    refresh_demo_scenario_freshness(db_session)

    latest = (
        db_session.query(PedestrianObservation)
        .filter(PedestrianObservation.sensor_id == demo_sensor.id)
        .order_by(PedestrianObservation.observed_at.desc())
        .first()
    )
    assert (datetime.now(timezone.utc) - latest.observed_at) < timedelta(minutes=1)


def test_refresh_is_a_no_op_with_no_demo_sensors(db_session):
    _add_sensor_with_observations(db_session, "api-test-sensor")
    assert refresh_demo_scenario_freshness(db_session) == 0
