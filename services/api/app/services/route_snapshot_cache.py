"""Persists fetched route snapshots for pinned demo (origin, destination)
pairs so seed.py and the live API process (two separate processes) agree on
exactly the same route geometry - see CachedSnapshotRoutingProvider in
routing_adapter.py for why this matters against a live, non-deterministic
provider like Google Directions."""
import json
from pathlib import Path

from app.services.routing_adapter import CandidateRoute, RouteSegmentGeometry

CACHE_PATH = Path(__file__).resolve().parents[2] / "demo_route_cache.json"
COORD_PRECISION = 4  # ~11m; matches demo scenario coordinates exactly


def route_pair_key(origin: tuple[float, float], destination: tuple[float, float]) -> str:
    """Public so other lookups keyed on the same (origin, destination) pair
    (e.g. seed.py's scenario-key index, used to scope demo sensor matching)
    round coordinates identically to the snapshot cache."""
    o_lat, o_lon = origin
    d_lat, d_lon = destination
    return f"{o_lat:.{COORD_PRECISION}f},{o_lon:.{COORD_PRECISION}f}->{d_lat:.{COORD_PRECISION}f},{d_lon:.{COORD_PRECISION}f}"


def _serialize(routes: list[CandidateRoute]) -> list[dict]:
    return [
        {
            "id": r.id,
            "name": r.name,
            "duration_minutes": r.duration_minutes,
            "distance_meters": r.distance_meters,
            "polyline": [list(p) for p in r.polyline],
            "segments": [{"sequence": s.sequence, "polyline": [list(p) for p in s.polyline]} for s in r.segments],
        }
        for r in routes
    ]


def _deserialize(data: list[dict]) -> list[CandidateRoute]:
    return [
        CandidateRoute(
            id=d["id"],
            name=d["name"],
            duration_minutes=d["duration_minutes"],
            distance_meters=d["distance_meters"],
            polyline=[(p[0], p[1]) for p in d["polyline"]],
            segments=[
                RouteSegmentGeometry(sequence=s["sequence"], polyline=[(p[0], p[1]) for p in s["polyline"]])
                for s in d["segments"]
            ],
        )
        for d in data
    ]


def _load_all() -> dict:
    if not CACHE_PATH.exists():
        return {}
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_snapshot(
    origin: tuple[float, float], destination: tuple[float, float], routes: list[CandidateRoute]
) -> None:
    cache = _load_all()
    cache[route_pair_key(origin, destination)] = _serialize(routes)
    CACHE_PATH.write_text(json.dumps(cache), encoding="utf-8")


def get_snapshot(origin: tuple[float, float], destination: tuple[float, float]) -> list[CandidateRoute] | None:
    data = _load_all().get(route_pair_key(origin, destination))
    return _deserialize(data) if data is not None else None
