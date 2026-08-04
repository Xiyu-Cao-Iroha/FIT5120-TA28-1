"""Loads demo pedestrian sensor/observation data so local runs have
something for the classifier to work against, standing in for the real
City of Melbourne ingestion pipeline (FR-03) until that data source is
confirmed (requirements section 20).

Usage: py -m app.seed   (run from services/api, with the venv active)
"""
import uuid
from datetime import datetime, timedelta, timezone

from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import ClassificationRule, DataSource, PedestrianObservation, PedestrianSensor, Place
from app.services.geo import point_to_polyline_distance_meters
from app.services.routing_adapter import DemoMelbourneCbdRoutingProvider

# Matches the pair used for manual/browser verification of the MVP journey.
DEMO_ORIGIN = (-37.8183, 144.9671)  # Flinders Street Station area
DEMO_DESTINATION = (-37.8095, 144.9646)  # State Library Victoria area

BUSY_CORRIDOR_COUNT = 170  # pedestrians / 5 min -> High Sensory
CALM_STREET_COUNT = 25  # pedestrians / 5 min -> Low Sensory

# US 2.1 / FR-09 demo refuge candidates, matching the Figma prototype
# exactly (name, address, and copy). State Library is flagged "verified"
# since it is a real, addressable public building; the other two are
# marked "prototype" per product principle 14.2 (describe conservatively,
# don't overstate what's actually confirmed).
DEMO_REFUGES = [
    {
        "external_id": "demo-refuge-state-library",
        "name": "State Library Victoria",
        "category": "library",
        "address": "328 Swanston Street, Melbourne",
        "lat": -37.8095,
        "lon": 144.9646,
        "short_description": "A quiet indoor space with seating and accessible facilities.",
        "facility_info": "Seating, accessible toilets and quieter areas are available during opening hours.",
        "data_source": "verified",
        "source_note": "Location information from selected City of Melbourne public datasets.",
    },
    {
        "external_id": "demo-refuge-st-francis",
        "name": "St Francis' Church Courtyard",
        "category": "courtyard",
        "address": "326 Lonsdale Street, Melbourne",
        "lat": -37.8117,
        "lon": 144.9631,
        "short_description": "A sheltered courtyard with seating away from the busiest foot traffic.",
        "facility_info": "Sheltered seating offers a quieter pause before continuing to State Library.",
        "data_source": "prototype",
        "source_note": "Prototype location information for demonstration.",
    },
    {
        "external_id": "demo-refuge-immigration-museum",
        "name": "Immigration Museum Courtyard",
        "category": "museum",
        "address": "400 Flinders Street, Melbourne",
        "lat": -37.8177,
        "lon": 144.9651,
        "short_description": "A sheltered outdoor space with seating and accessible facilities.",
        "facility_info": "Courtyard seating and accessible facilities are available during museum opening hours.",
        "data_source": "prototype",
        "source_note": "Prototype location information for demonstration.",
    },
]

# Minimum distance a sensor must sit from the *other* candidate route before
# it is seeded, so a sensor placed for one route can never also match a
# segment of the other route. Comfortably larger than the default
# sensor_match_radius_meters (see app/config.py).
MIN_SEPARATION_FROM_OTHER_ROUTE_M = 100.0


def _points_clear_of(polyline: list[tuple[float, float]], other_polyline: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Interior points of `polyline` that stay outside the match radius of
    `other_polyline`, so seeding stays purely per-route regardless of the
    exact demo route geometry."""
    return [
        point
        for point in polyline[1:-1]
        if point_to_polyline_distance_meters(point, other_polyline) >= MIN_SEPARATION_FROM_OTHER_ROUTE_M
    ]


def _add_sensor(db: Session, external_id: str, name: str, lat: float, lon: float) -> PedestrianSensor:
    sensor = PedestrianSensor(
        id=uuid.uuid4(),
        external_id=external_id,
        name=name,
        geom=from_shape(Point(lon, lat), srid=4326),
        active=True,
    )
    db.add(sensor)
    return sensor


def _add_observations(db: Session, sensor: PedestrianSensor, count: int, now: datetime, n: int = 3) -> None:
    for i in range(n):
        db.add(
            PedestrianObservation(
                id=uuid.uuid4(),
                sensor_id=sensor.id,
                observed_at=now - timedelta(minutes=5 * i),
                count=count,
                interval_minutes=5,
                quality_flag="ok",
            )
        )


def seed() -> None:
    db = SessionLocal()
    now = datetime.now(timezone.utc)
    try:
        if db.query(DataSource).count() == 0:
            db.add(
                DataSource(
                    id=uuid.uuid4(),
                    name="City of Melbourne Pedestrian Counting System (demo)",
                    url="https://data.melbourne.vic.gov.au/",
                    licence="CC BY 4.0",
                    refresh_interval_minutes=15,
                )
            )

        if db.query(ClassificationRule).count() == 0:
            db.add(
                ClassificationRule(
                    id=uuid.uuid4(),
                    version="v1",
                    crowd_score_threshold=0.6,
                    min_data_coverage=0.5,
                    max_observation_age_minutes=30,
                    active=True,
                )
            )

        if db.query(Place).count() == 0:
            for refuge in DEMO_REFUGES:
                db.add(
                    Place(
                        id=uuid.uuid4(),
                        source_external_id=refuge["external_id"],
                        name=refuge["name"],
                        category=refuge["category"],
                        address=refuge["address"],
                        geom=from_shape(Point(refuge["lon"], refuge["lat"]), srid=4326),
                        place_metadata={
                            "short_description": refuge["short_description"],
                            "facility_info": refuge["facility_info"],
                            "data_source": refuge["data_source"],
                            "source_note": refuge["source_note"],
                        },
                    )
                )
            print(f"Seeded {len(DEMO_REFUGES)} demo refuge places.")
        else:
            print("Refuge places already seeded, skipping.")

        if db.query(PedestrianSensor).count() > 0:
            print("Sensors already seeded, skipping sensor/observation seed.")
            db.commit()
            return

        provider = DemoMelbourneCbdRoutingProvider()
        direct, alternate = provider.get_candidate_routes(DEMO_ORIGIN, DEMO_DESTINATION)

        # Only seed points that stay clear of the other route's line, so a
        # sensor placed for one candidate route can never also match a
        # segment of the other one (see route_comparison.py's averaging note
        # for why a little boundary contamination would otherwise matter).
        direct_points = _points_clear_of(direct.polyline, alternate.polyline)
        alternate_points = _points_clear_of(alternate.polyline, direct.polyline)

        for i, (lat, lon) in enumerate(direct_points, start=1):
            sensor = _add_sensor(db, f"demo-direct-{i}", f"Direct corridor sensor {i}", lat, lon)
            _add_observations(db, sensor, count=BUSY_CORRIDOR_COUNT, now=now)

        for i, (lat, lon) in enumerate(alternate_points, start=1):
            sensor = _add_sensor(db, f"demo-alt-{i}", f"Side street sensor {i}", lat, lon)
            _add_observations(db, sensor, count=CALM_STREET_COUNT, now=now)

        db.commit()
        print(f"Seeded {len(direct_points)} direct-corridor sensors and {len(alternate_points)} side-street sensors.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
