import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

import httpx

from app.services.geo import haversine_distance_meters
from app.services.polyline import decode_polyline

logger = logging.getLogger(__name__)

WALKING_METERS_PER_MINUTE = 80.0
SEGMENT_LENGTH_METERS = 120.0
GOOGLE_DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json"


@dataclass(frozen=True)
class RouteSegmentGeometry:
    sequence: int
    polyline: list[tuple[float, float]]  # [(lat, lon), ...]


@dataclass(frozen=True)
class CandidateRoute:
    id: str
    name: str
    duration_minutes: float
    distance_meters: float
    polyline: list[tuple[float, float]]
    segments: list[RouteSegmentGeometry]


class RoutingProvider(ABC):
    """Isolates the routing backend behind a stable interface (FR-02) so a
    production provider can replace the demo implementation without any
    change to the client-facing API contract."""

    @abstractmethod
    def get_candidate_routes(
        self, origin: tuple[float, float], destination: tuple[float, float]
    ) -> list[CandidateRoute]:
        raise NotImplementedError


def build_candidate_route(
    route_id: str,
    name: str,
    waypoints: list[tuple[float, float]],
    duration_minutes: float | None = None,
    distance_meters: float | None = None,
) -> CandidateRoute:
    """Chops raw waypoints into ~120m sub-segments so congestion can be
    localised (FR-04: "divided into analysable segments") rather than
    collapsing an entire multi-block route into a single segment. Duration
    and distance are computed from the geometry unless a provider (e.g.
    Google Directions) already supplies real ones."""
    distance = distance_meters if distance_meters is not None else _polyline_length_m(waypoints)
    duration = duration_minutes if duration_minutes is not None else round(distance / WALKING_METERS_PER_MINUTE, 1)

    dense_points = _subdivide_polyline(waypoints, segment_length_m=SEGMENT_LENGTH_METERS)
    segments = [
        RouteSegmentGeometry(sequence=i, polyline=[dense_points[i], dense_points[i + 1]])
        for i in range(len(dense_points) - 1)
    ]
    return CandidateRoute(
        id=route_id,
        name=name,
        duration_minutes=round(duration, 1),
        distance_meters=round(distance, 1),
        polyline=dense_points,
        segments=segments,
    )


class DemoMelbourneCbdRoutingProvider(RoutingProvider):
    """Controlled demonstration routes for the onboarding MVP (FR-02), used
    until a production routing provider is confirmed - see requirements
    section 19-20, "routing provider not confirmed"."""

    def get_candidate_routes(
        self, origin: tuple[float, float], destination: tuple[float, float]
    ) -> list[CandidateRoute]:
        o_lat, o_lon = origin
        d_lat, d_lon = destination

        direct_polyline = [origin, destination]
        # Offset midpoint to create a distinct "alternate" walking path, far
        # enough from the direct line that a seeded demo scenario can give
        # each route its own, non-overlapping sensor coverage.
        mid = ((o_lat + d_lat) / 2 + 0.0035, (o_lon + d_lon) / 2 - 0.0035)
        alternate_polyline = [origin, mid, destination]

        return [
            build_candidate_route("route-direct", "Direct route via main corridor", direct_polyline),
            build_candidate_route("route-alternate", "Alternate route via side streets", alternate_polyline),
        ]


class GoogleDirectionsRoutingProvider(RoutingProvider):
    """FR-02: production routing provider backed by the Google Maps
    Platform Directions API (walking mode, alternatives requested). Only
    used when GOOGLE_MAPS_API_KEY is configured - see app/config.py."""

    def __init__(self, api_key: str, timeout_seconds: float = 8.0):
        self._api_key = api_key
        self._timeout = timeout_seconds

    def get_candidate_routes(
        self, origin: tuple[float, float], destination: tuple[float, float]
    ) -> list[CandidateRoute]:
        params = {
            "origin": f"{origin[0]},{origin[1]}",
            "destination": f"{destination[0]},{destination[1]}",
            "mode": "walking",
            "alternatives": "true",
            "key": self._api_key,
        }
        try:
            response = httpx.get(GOOGLE_DIRECTIONS_URL, params=params, timeout=self._timeout)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError:
            logger.exception("Google Directions API request failed")
            return []

        if payload.get("status") != "OK":
            logger.warning("Google Directions API returned status=%s", payload.get("status"))
            return []

        routes: list[CandidateRoute] = []
        for i, route in enumerate(payload.get("routes", [])):
            legs = route.get("legs", [])
            if not legs:
                continue
            leg = legs[0]
            encoded = route.get("overview_polyline", {}).get("points")
            if not encoded:
                continue
            waypoints = decode_polyline(encoded)
            if len(waypoints) < 2:
                continue

            summary = route.get("summary") or f"Walking route {i + 1}"
            routes.append(
                build_candidate_route(
                    route_id=f"route-{i + 1}",
                    name=f"Route via {summary}" if route.get("summary") else summary,
                    waypoints=waypoints,
                    duration_minutes=leg.get("duration", {}).get("value", 0) / 60,
                    distance_meters=leg.get("distance", {}).get("value", 0),
                )
            )
        return routes


class CachedSnapshotRoutingProvider(RoutingProvider):
    """Wraps another provider: for a pinned (origin, destination) pair with
    a saved snapshot, replays it instead of calling the inner provider
    again. A live provider like Google Directions isn't guaranteed to
    return byte-identical alternatives (same routes, same order) between
    two separate calls - without this, seed.py's sensor placement (one API
    call) can silently drift from what a later live comparison request
    (a different API call) actually returns, breaking the intended demo
    outcome. Any (origin, destination) without a snapshot passes straight
    through, so ad-hoc searches stay fully live."""

    def __init__(self, inner: RoutingProvider):
        self.inner = inner

    def get_candidate_routes(
        self, origin: tuple[float, float], destination: tuple[float, float]
    ) -> list[CandidateRoute]:
        from app.services.route_snapshot_cache import get_snapshot

        cached = get_snapshot(origin, destination)
        if cached is not None:
            return cached
        return self.inner.get_candidate_routes(origin, destination)


def get_routing_provider(api_key: str | None, timeout_seconds: float = 8.0) -> RoutingProvider:
    """Section 20 decision #3: routing provider selection. Demo routes back
    the MVP until a production provider is confirmed; set
    GOOGLE_MAPS_API_KEY to switch to real routing with no other change.
    Wrapped in CachedSnapshotRoutingProvider so pinned demo pairs (see
    app/seed.py) stay perfectly repeatable regardless of provider."""
    base = GoogleDirectionsRoutingProvider(api_key, timeout_seconds) if api_key else DemoMelbourneCbdRoutingProvider()
    return CachedSnapshotRoutingProvider(base)


def _polyline_length_m(polyline: list[tuple[float, float]]) -> float:
    total = 0.0
    for (lat1, lon1), (lat2, lon2) in zip(polyline, polyline[1:]):
        total += haversine_distance_meters(lat1, lon1, lat2, lon2)
    return total


def _interpolate(a: tuple[float, float], b: tuple[float, float], t: float) -> tuple[float, float]:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _subdivide_polyline(polyline: list[tuple[float, float]], segment_length_m: float) -> list[tuple[float, float]]:
    points = [polyline[0]]
    for p1, p2 in zip(polyline, polyline[1:]):
        leg_length = haversine_distance_meters(p1[0], p1[1], p2[0], p2[1])
        if leg_length == 0:
            continue
        steps = max(1, round(leg_length / segment_length_m))
        for i in range(1, steps + 1):
            points.append(_interpolate(p1, p2, i / steps))
    return points
