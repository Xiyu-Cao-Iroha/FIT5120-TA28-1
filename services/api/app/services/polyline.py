def decode_polyline(encoded: str) -> list[tuple[float, float]]:
    """Decodes Google's polyline algorithm format into [(lat, lon), ...].

    https://developers.google.com/maps/documentation/utilities/polylinealgorithm
    """
    points: list[tuple[float, float]] = []
    index = lat = lon = 0
    length = len(encoded)

    while index < length:
        for is_lat in (True, False):
            shift = result = 0
            while True:
                byte = ord(encoded[index]) - 63
                index += 1
                result |= (byte & 0x1F) << shift
                shift += 5
                if byte < 0x20:
                    break
            delta = ~(result >> 1) if result & 1 else (result >> 1)
            if is_lat:
                lat += delta
            else:
                lon += delta
        points.append((lat / 1e5, lon / 1e5))

    return points
