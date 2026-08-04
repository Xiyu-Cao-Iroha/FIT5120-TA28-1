from app.services.polyline import decode_polyline


def test_decodes_known_google_example():
    # From Google's own polyline algorithm documentation.
    encoded = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"
    points = decode_polyline(encoded)
    assert len(points) == 3
    (lat1, lon1), (lat2, lon2), (lat3, lon3) = points
    assert lat1 == 38.5
    assert lon1 == -120.2
    assert lat2 == 40.7
    assert lon2 == -120.95
    assert lat3 == 43.252
    assert lon3 == -126.453


def test_empty_string_decodes_to_empty_list():
    assert decode_polyline("") == []
