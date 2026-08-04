from dataclasses import dataclass

from geoalchemy2.shape import to_shape
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Place
from app.services.geo import parse_linestring_wkt, point_to_polyline_distance_meters

MAX_REFUGE_DISTANCE_METERS = 500.0
MAX_REFUGE_RESULTS = 5


@dataclass(frozen=True)
class RefugeCandidate:
    place: Place
    distance_meters: float


def find_refuges_near_route(db: Session, route_geometry_wkt: str) -> list[RefugeCandidate]:
    """FR-09: search for candidate refuge locations near the selected route.
    Empty results are valid (renders as the 'No quiet places nearby' state) -
    this must never invent a location to fill the list."""
    polyline = parse_linestring_wkt(route_geometry_wkt)
    if not polyline:
        return []

    places = db.execute(select(Place)).scalars().all()
    candidates: list[RefugeCandidate] = []
    for place in places:
        point = to_shape(place.geom)  # shapely Point(x=lon, y=lat)
        distance = point_to_polyline_distance_meters((point.y, point.x), polyline)
        if distance <= MAX_REFUGE_DISTANCE_METERS:
            candidates.append(RefugeCandidate(place=place, distance_meters=distance))

    candidates.sort(key=lambda c: c.distance_meters)
    return candidates[:MAX_REFUGE_RESULTS]


def find_refuge_distance(db: Session, place_id, route_geometry_wkt: str) -> float | None:
    place = db.get(Place, place_id)
    if place is None:
        return None
    polyline = parse_linestring_wkt(route_geometry_wkt)
    if not polyline:
        return None
    point = to_shape(place.geom)
    return point_to_polyline_distance_meters((point.y, point.x), polyline)
