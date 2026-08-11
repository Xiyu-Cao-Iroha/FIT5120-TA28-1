export function parseLineStringWkt(wkt: string): { lon: number; lat: number }[] {
  const match = wkt.match(/^LINESTRING\s*\((.+)\)$/i);
  if (!match) return [];
  return match[1]
    .split(",")
    .map((pair) => pair.trim().split(/\s+/).map(Number))
    .filter(([lon, lat]) => Number.isFinite(lon) && Number.isFinite(lat))
    .map(([lon, lat]) => ({ lon, lat }));
}

const EARTH_RADIUS_METERS = 6371000;

function haversineMeters(a: { lat: number; lon: number }, b: { lat: number; lon: number }): number {
  const toRad = (deg: number) => (deg * Math.PI) / 180;
  const dLat = toRad(b.lat - a.lat);
  const dLon = toRad(b.lon - a.lon);
  const h =
    Math.sin(dLat / 2) ** 2 + Math.cos(toRad(a.lat)) * Math.cos(toRad(b.lat)) * Math.sin(dLon / 2) ** 2;
  return 2 * EARTH_RADIUS_METERS * Math.asin(Math.sqrt(h));
}

// Route segments vary a lot in real length (Google's polyline has many short
// legs near corners/crossings, each still gets its own segment) - so a
// segment count can't be turned into a distance via a fixed per-segment
// constant. Measuring the actual geometry is the only accurate way.
export function lineStringLengthMeters(wkt: string): number {
  const points = parseLineStringWkt(wkt);
  let total = 0;
  for (let i = 1; i < points.length; i++) {
    total += haversineMeters(points[i - 1], points[i]);
  }
  return total;
}
