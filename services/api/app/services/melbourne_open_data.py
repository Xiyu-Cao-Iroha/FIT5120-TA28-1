import logging
from datetime import datetime, timedelta

import httpx

from app.services.geo import point_to_polyline_distance_meters
from app.services.pedestrian_repository import REFERENCE_CAPACITY_COUNT, SegmentPedestrianStats

logger = logging.getLogger(__name__)

API_BASE_URL = "https://data.melbourne.vic.gov.au/api/explore/v2.1/catalog/datasets"
SENSOR_LOCATIONS_DATASET = "pedestrian-counting-system-sensor-locations"
MINUTE_COUNTS_DATASET = "pedestrian-counting-system-past-hour-counts-per-minute"

# The Explore API v2.1 rejects any limit above 100 (InvalidRESTParameterError),
# so fetching "recent counts across ~100 CBD sensors" needs pagination.
PAGE_SIZE = 100
MAX_PAGES = 10

# The counts dataset reports pedestrians per *minute*, but REFERENCE_CAPACITY_COUNT
# (pedestrian_repository.py) is calibrated against 5-minute observation windows to
# match the seeded demo data. Scale live per-minute counts up before comparing them
# on the same threshold, or every live route would read as artificially calm.
DEMO_INTERVAL_MINUTES = 5


class MelbourneOpenDataPedestrianRepository:
    """Live pedestrian crowd data straight from the City of Melbourne open data
    portal's Pedestrian Counting System - no API key needed, it's public.

    Fetches sensor locations and recent per-minute counts once per request
    (cached on this instance) rather than per segment, since a route can have
    a dozen-plus segments and a fresh HTTP round trip per segment would be
    both slow and unnecessarily hard on a public API.

    Never used for pinned demo (origin, destination) pairs - route_comparison.py
    always routes those to the seeded PedestrianDataRepository instead, so
    demo scenarios stay reliable for a presentation regardless of network
    conditions or upstream API availability.
    """

    def __init__(
        self,
        match_radius_meters: float,
        max_observation_age_minutes: int,
        cbd_bounds: tuple[float, float, float, float],
        timeout_seconds: float = 8.0,
    ):
        self.match_radius_meters = match_radius_meters
        self.max_age = timedelta(minutes=max_observation_age_minutes)
        self.min_lat, self.max_lat, self.min_lon, self.max_lon = cbd_bounds
        self.timeout = timeout_seconds
        self._sensors: list[dict] | None = None
        self._counts_by_location: dict[int, list[int]] | None = None

    def _ensure_loaded(self, now: datetime) -> None:
        if self._sensors is not None:
            return
        self._sensors = self._fetch_sensors()
        location_ids = [s["location_id"] for s in self._sensors]
        self._counts_by_location = self._fetch_recent_counts(location_ids, now)

    def _fetch_sensors(self) -> list[dict]:
        where = (
            f"latitude>{self.min_lat} and latitude<{self.max_lat} "
            f"and longitude>{self.min_lon} and longitude<{self.max_lon} and status='A'"
        )
        try:
            response = httpx.get(
                f"{API_BASE_URL}/{SENSOR_LOCATIONS_DATASET}/records",
                params={"where": where, "limit": 100},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json().get("results", [])
        except httpx.HTTPError:
            logger.exception("Melbourne open data sensor-locations request failed")
            return []

    def _fetch_recent_counts(self, location_ids: list[int], now: datetime) -> dict[int, list[int]]:
        if not location_ids:
            return {}
        ids_csv = ",".join(str(i) for i in location_ids)
        cutoff = now - self.max_age
        by_location: dict[int, list[int]] = {}

        # Sorted newest-first, so once a page's oldest row is past the cutoff
        # there is nothing more recent left to find - stop instead of paging
        # through the rest of the "past hour" dataset for no benefit.
        for page in range(MAX_PAGES):
            try:
                response = httpx.get(
                    f"{API_BASE_URL}/{MINUTE_COUNTS_DATASET}/records",
                    params={
                        "where": f"location_id in ({ids_csv})",
                        "order_by": "sensing_datetime desc",
                        "limit": PAGE_SIZE,
                        "offset": page * PAGE_SIZE,
                    },
                    timeout=self.timeout,
                )
                response.raise_for_status()
                results = response.json().get("results", [])
            except httpx.HTTPError:
                logger.exception("Melbourne open data pedestrian-counts request failed")
                break

            if not results:
                break

            reached_cutoff = False
            for row in results:
                observed_at = datetime.fromisoformat(row["sensing_datetime"])
                if observed_at < cutoff:
                    reached_cutoff = True
                    break
                by_location.setdefault(row["location_id"], []).append(row["total_of_directions"])

            if reached_cutoff or len(results) < PAGE_SIZE:
                break

        return by_location

    def stats_for_segment(
        self,
        polyline: list[tuple[float, float]],
        now: datetime,
        sensor_external_id_prefix: str | None = None,
    ) -> SegmentPedestrianStats:
        self._ensure_loaded(now)

        matched_sensor_count = 0
        matched_counts: list[int] = []
        for sensor in self._sensors:
            point = (sensor["latitude"], sensor["longitude"])
            if point_to_polyline_distance_meters(point, polyline) <= self.match_radius_meters:
                matched_sensor_count += 1
                matched_counts.extend(self._counts_by_location.get(sensor["location_id"], []))

        if matched_sensor_count == 0:
            return SegmentPedestrianStats(sensor_count=0, crowd_score=None, has_coverage=False)
        if not matched_counts:
            return SegmentPedestrianStats(sensor_count=matched_sensor_count, crowd_score=None, has_coverage=False)

        avg_per_minute = sum(matched_counts) / len(matched_counts)
        crowd_score = min(1.0, (avg_per_minute * DEMO_INTERVAL_MINUTES) / REFERENCE_CAPACITY_COUNT)
        return SegmentPedestrianStats(sensor_count=matched_sensor_count, crowd_score=crowd_score, has_coverage=True)
