from fastapi import APIRouter, Depends, Query

from app.config import Settings, get_settings
from app.errors import ApiError
from app.schemas import PlaceSearchResponse, PlaceSuggestion, ResolvedPlace
from app.services.places_provider import get_places_provider

router = APIRouter()


class PlaceNotFoundError(ApiError):
    def __init__(self, message: str = "Place not found."):
        super().__init__(404, "PLACE_NOT_FOUND", message)


@router.get("/places/search", response_model=PlaceSearchResponse)
def search_places(query: str = Query(..., min_length=1), settings: Settings = Depends(get_settings)) -> PlaceSearchResponse:
    provider = get_places_provider(settings.google_maps_api_key, settings.google_maps_request_timeout_seconds)
    suggestions = provider.search(query)
    return PlaceSearchResponse(
        suggestions=[PlaceSuggestion(place_id=s.place_id, description=s.description) for s in suggestions]
    )


@router.get("/places/resolve", response_model=ResolvedPlace)
def resolve_place(place_id: str = Query(...), settings: Settings = Depends(get_settings)) -> ResolvedPlace:
    provider = get_places_provider(settings.google_maps_api_key, settings.google_maps_request_timeout_seconds)
    resolved = provider.resolve(place_id)
    if resolved is None:
        raise PlaceNotFoundError()
    return ResolvedPlace(
        place_id=resolved.place_id, description=resolved.description, lat=resolved.lat, lon=resolved.lon
    )
