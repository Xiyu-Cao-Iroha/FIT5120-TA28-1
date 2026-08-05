from dataclasses import dataclass
from datetime import datetime, timedelta

from geoalchemy2.shape import to_shape
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import PedestrianObservation, PedestrianSensor
from app.services.geo import point_to_polyline_distance_meters

# Pedestrians per interval treated as "fully congested" (crowd_score 1.0).
# Placeholder pending requirements section 20 decision #2 (threshold owner).
REFERENCE_CAPACITY_COUNT = 120.0


@dataclass(frozen=True)
class SegmentPedestrianStats:
    sensor_count: int
    crowd_score: float | None
    has_coverage: bool


class PedestrianDataRepository:
    """FR-03/FR-04: matches route segments to nearby sensors and summarises
    recent observations into a crowd score.

    Backed by Postgres today but isolated behind this class so a future
    direct City of Melbourne API client (or a caching layer) can replace
    the implementation without changing callers such as route_comparison.
    """

    def __init__(self, db: Session, match_radius_meters: float, max_observation_age_minutes: int):
        self.db = db
        self.match_radius_meters = match_radius_meters
        self.max_age = timedelta(minutes=max_observation_age_minutes)

    def stats_for_segment(
        self,
        polyline: list[tuple[float, float]],
        now: datetime,
        sensor_external_id_prefix: str | None = None,
    ) -> SegmentPedestrianStats:
        query = select(PedestrianSensor).where(PedestrianSensor.active.is_(True))
        if sensor_external_id_prefix is not None:
            # Scopes matching to one demo scenario's own sensors so
            # overlapping CBD streets (e.g. several scenarios walking along
            # Swanston St) don't leak another scenario's crowd counts into
            # this route's score - see route_comparison._demo_sensor_prefix.
            query = query.where(PedestrianSensor.external_id.like(f"{sensor_external_id_prefix}%"))
        sensors = self.db.execute(query).scalars().all()

        matched_ids = []
        for sensor in sensors:
            point = to_shape(sensor.geom)  # shapely Point(x=lon, y=lat)
            distance = point_to_polyline_distance_meters((point.y, point.x), polyline)
            if distance <= self.match_radius_meters:
                matched_ids.append(sensor.id)

        if not matched_ids:
            return SegmentPedestrianStats(sensor_count=0, crowd_score=None, has_coverage=False)

        cutoff = now - self.max_age
        observations = self.db.execute(
            select(PedestrianObservation).where(
                PedestrianObservation.sensor_id.in_(matched_ids),
                PedestrianObservation.observed_at >= cutoff,
                PedestrianObservation.quality_flag == "ok",
            )
        ).scalars().all()

        if not observations:
            return SegmentPedestrianStats(sensor_count=len(matched_ids), crowd_score=None, has_coverage=False)

        avg_count = sum(o.count for o in observations) / len(observations)
        crowd_score = min(1.0, avg_count / REFERENCE_CAPACITY_COUNT)
        return SegmentPedestrianStats(
            sensor_count=len(matched_ids), crowd_score=crowd_score, has_coverage=True
        )
