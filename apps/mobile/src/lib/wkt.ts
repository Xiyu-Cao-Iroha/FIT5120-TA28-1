export function parseLineStringWkt(wkt: string): { lon: number; lat: number }[] {
  const match = wkt.match(/^LINESTRING\s*\((.+)\)$/i);
  if (!match) return [];
  return match[1]
    .split(",")
    .map((pair) => pair.trim().split(/\s+/).map(Number))
    .filter(([lon, lat]) => Number.isFinite(lon) && Number.isFinite(lat))
    .map(([lon, lat]) => ({ lon, lat }));
}
