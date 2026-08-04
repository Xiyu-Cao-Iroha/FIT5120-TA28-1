import math
import re

EARTH_RADIUS_M = 6_371_000.0

_LINESTRING_PATTERN = re.compile(r"^LINESTRING\s*\((.+)\)$", re.IGNORECASE)


def parse_linestring_wkt(wkt: str) -> list[tuple[float, float]]:
    """Parses 'LINESTRING(lon lat, lon lat, ...)' into [(lat, lon), ...]."""
    match = _LINESTRING_PATTERN.match(wkt.strip())
    if not match:
        return []
    points = []
    for pair in match.group(1).split(","):
        parts = pair.strip().split()
        if len(parts) != 2:
            continue
        lon, lat = float(parts[0]), float(parts[1])
        points.append((lat, lon))
    return points


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(min(1.0, a)))


def point_to_polyline_distance_meters(
    point: tuple[float, float], polyline: list[tuple[float, float]]
) -> float:
    """Approximate min distance (meters) from a (lat, lon) point to a polyline
    of (lat, lon) vertices, via a local equirectangular projection anchored
    at the polyline's first vertex. Accurate at CBD scale (a few km)."""
    lat0, lon0 = polyline[0]

    def project(lat: float, lon: float) -> tuple[float, float]:
        x = math.radians(lon - lon0) * math.cos(math.radians(lat0)) * EARTH_RADIUS_M
        y = math.radians(lat - lat0) * EARTH_RADIUS_M
        return x, y

    px, py = project(*point)
    best = math.inf
    for (lat1, lon1), (lat2, lon2) in zip(polyline, polyline[1:]):
        x1, y1 = project(lat1, lon1)
        x2, y2 = project(lat2, lon2)
        dx, dy = x2 - x1, y2 - y1
        seg_len_sq = dx * dx + dy * dy
        t = 0.0 if seg_len_sq == 0 else max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / seg_len_sq))
        cx, cy = x1 + t * dx, y1 + t * dy
        best = min(best, math.hypot(px - cx, py - cy))
    return best
