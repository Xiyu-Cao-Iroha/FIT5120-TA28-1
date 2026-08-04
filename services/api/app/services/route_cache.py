from app.schemas import RouteOptionOut

# Cache of the most recent comparison's routes, keyed by route id, so
# GET /routes/{id} and GET /refuges can serve detail without re-running the
# comparison. In-process only - acceptable for the single-instance
# onboarding MVP; a multi-instance deploy would need a shared store.
_routes_by_id: dict[str, RouteOptionOut] = {}


def store_routes(routes: list[RouteOptionOut]) -> None:
    for route in routes:
        _routes_by_id[route.id] = route


def get_route(route_id: str) -> RouteOptionOut | None:
    return _routes_by_id.get(route_id)
