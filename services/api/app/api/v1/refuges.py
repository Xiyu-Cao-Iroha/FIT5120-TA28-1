from uuid import UUID

from fastapi import APIRouter, Depends, Query
from geoalchemy2.shape import to_shape
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import ApiError
from app.models import Place
from app.schemas import RefugeDetail, RefugeListResponse, RefugeSource, RefugeSummary
from app.services.refuge_repository import find_refuge_distance, find_refuges_near_route
from app.services.route_cache import get_route

router = APIRouter()


class RefugeNotFoundError(ApiError):
    def __init__(self, message: str = "Refuge location not found."):
        super().__init__(404, "REFUGE_NOT_FOUND", message)


class RouteNotCachedError(ApiError):
    def __init__(self, message: str = "Route not found. Run a comparison first."):
        super().__init__(404, "NO_ROUTE_FOUND", message)


def _to_summary(place: Place, distance_meters: float) -> RefugeSummary:
    point = to_shape(place.geom)  # shapely Point(x=lon, y=lat)
    meta = place.place_metadata or {}
    return RefugeSummary(
        id=str(place.id),
        name=place.name,
        category=place.category,
        address=place.address or "",
        lat=point.y,
        lon=point.x,
        distance_meters=round(distance_meters, 1),
        short_description=meta.get("short_description", ""),
        data_source=RefugeSource(meta.get("data_source", "prototype")),
    )


@router.get("/refuges", response_model=RefugeListResponse)
def list_refuges(route_id: str = Query(...), db: Session = Depends(get_db)) -> RefugeListResponse:
    route = get_route(route_id)
    if route is None:
        raise RouteNotCachedError()

    candidates = find_refuges_near_route(db, route.geometry)
    refuges = [_to_summary(c.place, c.distance_meters) for c in candidates]
    return RefugeListResponse(route_id=route_id, refuges=refuges)


@router.get("/refuges/{place_id}", response_model=RefugeDetail)
def get_refuge_detail(place_id: str, route_id: str = Query(...), db: Session = Depends(get_db)) -> RefugeDetail:
    try:
        place_uuid = UUID(place_id)
    except ValueError:
        raise RefugeNotFoundError() from None

    place = db.get(Place, place_uuid)
    if place is None:
        raise RefugeNotFoundError()

    route = get_route(route_id)
    if route is None:
        raise RouteNotCachedError()

    distance = find_refuge_distance(db, place_uuid, route.geometry)
    if distance is None:
        raise RefugeNotFoundError()

    summary = _to_summary(place, distance)
    meta = place.place_metadata or {}
    return RefugeDetail(
        **summary.model_dump(),
        facility_info=meta.get("facility_info", ""),
        source_note=meta.get("source_note", ""),
    )
