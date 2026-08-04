from app.schemas import SensoryLevel
from app.services.recommendation import RouteCandidate, apply_recommendation


def _candidate(id_, duration, score, level):
    return RouteCandidate(id=id_, name=id_, duration_minutes=duration, crowd_score=score, sensory_level=level)


def test_recommends_lowest_crowd_score():
    routes = [
        _candidate("a", 10, 0.7, SensoryLevel.high),
        _candidate("b", 15, 0.3, SensoryLevel.low),
    ]
    result = apply_recommendation(routes)
    assert next(r for r in result if r.id == "b").is_recommended
    assert not next(r for r in result if r.id == "a").is_recommended


def test_faster_but_more_congested_route_is_not_recommended():
    routes = [
        _candidate("fast", 8, 0.9, SensoryLevel.high),
        _candidate("slow", 14, 0.2, SensoryLevel.low),
    ]
    result = apply_recommendation(routes)
    winner = next(r for r in result if r.is_recommended)
    assert winner.id == "slow"


def test_single_route_unavailable_gets_no_sensory_recommendation():
    routes = [
        _candidate("a", 10, None, SensoryLevel.unavailable),
        _candidate("b", 12, 0.3, SensoryLevel.low),
    ]
    result = apply_recommendation(routes)
    unavailable = next(r for r in result if r.id == "a")
    assert not unavailable.is_recommended
    assert "unavailable" in unavailable.explanation.lower()
    assert next(r for r in result if r.id == "b").is_recommended


def test_all_routes_unavailable_yields_no_recommendation():
    routes = [
        _candidate("a", 10, None, SensoryLevel.unavailable),
        _candidate("b", 12, None, SensoryLevel.unavailable),
    ]
    result = apply_recommendation(routes)
    assert not any(r.is_recommended for r in result)


def test_all_routes_congested_recommends_comparatively_lower_and_says_so():
    routes = [
        _candidate("a", 10, 0.95, SensoryLevel.high),
        _candidate("b", 12, 0.65, SensoryLevel.high),
    ]
    result = apply_recommendation(routes)
    winner = next(r for r in result if r.is_recommended)
    assert winner.id == "b"
    assert "not congestion-free" in winner.explanation
