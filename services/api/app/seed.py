"""Loads demo pedestrian sensor/observation data so local runs have
something for the classifier to work against, standing in for the real
City of Melbourne ingestion pipeline (FR-03) until that data source is
confirmed (requirements section 20).

Seeds sensors along whichever routing provider is actually live (Google
Directions if GOOGLE_MAPS_API_KEY is set, the demo provider otherwise) -
using the real provider's own routes means the demo data lines up with
what a live comparison will actually return.

Usage: py -m app.seed   (run from services/api, with the venv active)
"""
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import SessionLocal
from app.models import ClassificationRule, DataSource, PedestrianObservation, PedestrianSensor, Place
from app.services.geo import point_to_polyline_distance_meters
from app.services.route_snapshot_cache import route_pair_key, save_snapshot
from app.services.routing_adapter import get_routing_provider

BUSY_CORRIDOR_COUNT = 170  # pedestrians / 5 min -> High Sensory
CALM_STREET_COUNT = 25  # pedestrians / 5 min -> Low Sensory

# Minimum distance a sensor must sit from any *other* candidate route in the
# same scenario before it is seeded, so a sensor placed for one route can
# never also match a segment of another route in the comparison. Just above
# sensor_match_radius_meters (app/config.py, 75m default) - a much larger
# margin over-excludes real Melbourne CBD streets, whose blocks are often
# only ~100-150m deep, leaving barely any usable points on a route that
# happens to run parallel to a sibling one street over.
MIN_SEPARATION_FROM_OTHER_ROUTE_M = 80.0


@dataclass(frozen=True)
class DemoScenario:
    key: str
    label: str
    origin: tuple[float, float]
    destination: tuple[float, float]
    # "contrast": first route busy, rest calm (Low vs High comparison).
    # "all_congested": every route busy (all-routes-congested state).
    # "one_unavailable": only the first route gets data, at a calm level
    #   (Low sensory next to Sensory information unavailable).
    mode: str


# A handful of real CBD pairs covering each of the comparison states the
# product needs to demonstrate (section 7 / AC 1.1.x, 1.2.x). "Use demo
# route" in the app defaults to the first one; the others are here so a
# presentation can show every state without hand-editing coordinates.
DEMO_SCENARIOS = [
    DemoScenario(
        key="southern-cross-state-library",
        label="Southern Cross Station -> State Library Victoria (Low vs High)",
        origin=(-37.8183, 144.9531),
        destination=(-37.8095, 144.9646),
        mode="contrast",
    ),
    DemoScenario(
        key="market-flinders",
        label="Queen Victoria Market -> Flinders Street Station (all congested)",
        origin=(-37.8076, 144.9568),
        destination=(-37.8183, 144.9671),
        mode="all_congested",
    ),
    DemoScenario(
        key="flinders-qv-market",
        label="Flinders Street Station -> Queen Victoria Market (one route unavailable)",
        origin=(-37.8183, 144.9671),
        destination=(-37.8076, 144.9568),
        mode="one_unavailable",
    ),
    DemoScenario(
        key="state-library-market",
        label="State Library Victoria -> Queen Victoria Market (Low vs High, near refuges)",
        origin=(-37.8095, 144.9646),
        destination=(-37.8076, 144.9568),
        mode="contrast",
    ),
]

# Looks up which pinned scenario a live (origin, destination) request
# matches, so route_comparison can scope sensor matching to that scenario's
# own sensors only - see route_comparison._demo_sensor_prefix.
DEMO_SCENARIO_KEY_BY_PAIR: dict[str, str] = {
    route_pair_key(s.origin, s.destination): s.key for s in DEMO_SCENARIOS
}

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


def _intended_count(mode: str, i: int) -> int | None:
    """The pedestrian count a route is meant to be seeded at, or None if it
    is meant to get no sensors at all (the "unavailable" route in
    one_unavailable mode)."""
    if mode == "all_congested":
        return BUSY_CORRIDOR_COUNT
    if mode == "one_unavailable":
        return CALM_STREET_COUNT if i == 0 else None
    return BUSY_CORRIDOR_COUNT if i == 0 else CALM_STREET_COUNT  # "contrast"


def _seed_scenario(db: Session, provider, scenario: DemoScenario, now: datetime) -> int:
    candidates = provider.get_candidate_routes(scenario.origin, scenario.destination)
    if not candidates:
        print(f"  ! no candidate routes for '{scenario.label}', skipping")
        return 0

    # Pin this exact set of routes so a later live /routes/compare for the
    # same pair replays it instead of asking Google again - see
    # CachedSnapshotRoutingProvider for why that matters.
    save_snapshot(scenario.origin, scenario.destination, candidates)

    routes_to_seed = candidates[:1] if scenario.mode == "one_unavailable" else candidates
    all_counts = [_intended_count(scenario.mode, i) for i in range(len(candidates))]
    total_sensors = 0

    for i, candidate in enumerate(routes_to_seed):
        count = all_counts[i]
        # Only keep a sensor away from a *different*-level sibling route
        # (e.g. this route's busy vs. a calm one, or an intentionally
        # data-free one in one_unavailable mode) - two same-level siblings
        # (both busy, or both calm) agreeing on nearby streets is harmless
        # and excluding between them just starves real Melbourne CBD
        # routes of coverage, since blocks there are often narrower than
        # MIN_SEPARATION_FROM_OTHER_ROUTE_M.
        other_polylines = [c.polyline for j, c in enumerate(candidates) if j != i and all_counts[j] != count]
        points = candidate.polyline[1:-1]
        if other_polylines:
            points = [
                p
                for p in points
                if all(
                    point_to_polyline_distance_meters(p, other) >= MIN_SEPARATION_FROM_OTHER_ROUTE_M
                    for other in other_polylines
                )
            ]

        for j, (lat, lon) in enumerate(points, start=1):
            sensor = _add_sensor(db, f"demo-{scenario.key}-r{i}-{j}", f"{scenario.label} sensor r{i}-{j}", lat, lon)
            _add_observations(db, sensor, count=count, now=now)
            total_sensors += 1

    return total_sensors


def seed() -> None:
    settings = get_settings()
    provider = get_routing_provider(settings.google_maps_api_key, settings.google_maps_request_timeout_seconds)
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

        # Pedestrian observations are time-sensitive (see
        # max_observation_age_minutes), so always reseed fresh rather than
        # skipping when sensors already exist from an earlier, now-stale run.
        db.query(PedestrianObservation).delete()
        db.query(PedestrianSensor).delete()

        print(f"Seeding demo scenarios via {type(provider).__name__}...")
        for scenario in DEMO_SCENARIOS:
            count = _seed_scenario(db, provider, scenario, now)
            print(f"  - {scenario.label}: {count} sensors")

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
