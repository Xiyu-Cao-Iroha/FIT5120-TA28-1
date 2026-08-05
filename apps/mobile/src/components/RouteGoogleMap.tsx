import { GoogleMap, Marker, Polyline } from "@react-google-maps/api";
import { useCallback, useMemo } from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";

import type { CongestedSegment } from "../api/schemas";
import { useGoogleMapsLoaded } from "../lib/googleMaps";
import { parseLineStringWkt } from "../lib/wkt";
import { colors } from "../theme/colors";

interface Props {
  routeGeometry: string;
  congestedSegments: CongestedSegment[];
}

const CONTAINER_STYLE = { width: "100%", height: 320 };

// FR-08: congested segments must be identifiable on the map. Real Google
// Maps view (web only, per product decision) - congested sub-paths are
// drawn as a second, differently-coloured polyline over the base route.
// Always paired with the equivalent text list in RouteMapScreen, since the
// map must not be the only way to understand the recommendation.
export function RouteGoogleMap({ routeGeometry, congestedSegments }: Props) {
  const { isLoaded, loadError } = useGoogleMapsLoaded();
  // Memoized on the raw inputs (not recomputed as fresh array/object
  // literals every render): @react-google-maps/api's Polyline diffs its
  // `path` prop via the underlying google.maps.MVCArray, and a new array
  // reference on every render - even with identical values, e.g. after an
  // unrelated parent re-render - can hit it mid-update and throw
  // "Cannot read properties of undefined (reading 'setAt')".
  const points = useMemo(() => parseLineStringWkt(routeGeometry), [routeGeometry]);
  const path = useMemo(() => points.map((p) => ({ lat: p.lat, lng: p.lon })), [points]);
  const congestedPaths = useMemo(
    () =>
      congestedSegments
        .map((segment) => ({
          sequence: segment.sequence,
          path: parseLineStringWkt(segment.geometry).map((p) => ({ lat: p.lat, lng: p.lon })),
        }))
        .filter((segment) => segment.path.length >= 2),
    [congestedSegments]
  );

  const onLoad = useCallback(
    (map: google.maps.Map) => {
      if (points.length < 2) return;
      const bounds = new google.maps.LatLngBounds();
      points.forEach((p) => bounds.extend({ lat: p.lat, lng: p.lon }));
      map.fitBounds(bounds, 40);
    },
    [points]
  );

  if (loadError) {
    return (
      <View style={styles.placeholder}>
        <Text style={styles.placeholderText}>Map failed to load.</Text>
      </View>
    );
  }

  if (!isLoaded || points.length < 2) {
    return (
      <View style={styles.placeholder}>
        <ActivityIndicator color={colors.primary} accessibilityLabel="Loading map" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <GoogleMap
        mapContainerStyle={CONTAINER_STYLE}
        center={path[0]}
        zoom={16}
        onLoad={onLoad}
        options={{ streetViewControl: false, mapTypeControl: false, fullscreenControl: false }}
      >
        <Polyline path={path} options={{ strokeColor: colors.calmLine, strokeWeight: 5, strokeOpacity: 0.9 }} />
        {congestedPaths.map((segment) => (
          <Polyline
            key={segment.sequence}
            path={segment.path}
            options={{ strokeColor: colors.congestedLine, strokeWeight: 6, strokeOpacity: 1 }}
          />
        ))}
        <Marker position={path[0]} label="A" title="Origin" />
        <Marker position={path[path.length - 1]} label="B" title="Destination" />
      </GoogleMap>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { borderRadius: 14, overflow: "hidden", borderWidth: 1, borderColor: colors.cardBorder },
  placeholder: {
    height: 320,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    backgroundColor: colors.cardBackground,
    alignItems: "center",
    justifyContent: "center",
  },
  placeholderText: { color: colors.caption, fontSize: 14 },
});
