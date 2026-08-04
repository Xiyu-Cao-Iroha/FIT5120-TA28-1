from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.errors import (
    DataSourceUnavailableError,
    InvalidLocationError,
    NoRouteFoundError,
    OutsideServiceAreaError,
    RateLimitedError,
)
from app.models import PedestrianSensor
from app.schemas import RouteCompareRequest, RouteCompareResponse, RouteDetailResponse
from app.services.rate_limit import get_rate_limiter
from app.services.route_cache import get_route, store_routes
from app.services.route_comparison import compare_routes
from app.services.routing_adapter import get_routing_provider

router = APIRouter()


def _validate_location(payload: RouteCompareRequest, settings: Settings) -> None:
    if payload.origin.lat == payload.destination.lat and payload.origin.lon == payload.destination.lon:
        raise InvalidLocationError()

    d = payload.destination
    within_cbd = (
        settings.cbd_min_lat <= d.lat <= settings.cbd_max_lat
        and settings.cbd_min_lon <= d.lon <= settings.cbd_max_lon
    )
    if not within_cbd:
        raise OutsideServiceAreaError()


@router.post("/routes/compare", response_model=RouteCompareResponse)
def post_routes_compare(
    payload: RouteCompareRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> RouteCompareResponse:
    limiter = get_rate_limiter(settings.rate_limit_per_minute)
    client_key = request.client.host if request.client else "anonymous"
    if not limiter.check(client_key):
        raise RateLimitedError()

    _validate_location(payload, settings)

    active_sensor_count = db.execute(
        select(func.count()).select_from(PedestrianSensor).where(PedestrianSensor.active.is_(True))
    ).scalar()
    if not active_sensor_count:
        raise DataSourceUnavailableError()

    routing_provider = get_routing_provider(settings.google_maps_api_key, settings.google_maps_request_timeout_seconds)
    result = compare_routes(
        db=db,
        settings=settings,
        routing_provider=routing_provider,
        origin=(payload.origin.lat, payload.origin.lon),
        destination=(payload.destination.lat, payload.destination.lon),
        crowd_sensitivity=payload.crowd_sensitivity,
    )

    if not result.routes:
        raise NoRouteFoundError()

    store_routes(result.routes)
    return result


@router.get("/routes/{route_id}", response_model=RouteDetailResponse)
def get_route_detail(route_id: str) -> RouteDetailResponse:
    route = get_route(route_id)
    if route is None:
        raise NoRouteFoundError(f"No cached route detail for id '{route_id}'. Run a comparison first.")
    return RouteDetailResponse(**route.model_dump())
