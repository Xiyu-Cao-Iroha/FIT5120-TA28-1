import { GoogleMap, Marker, Polyline } from "@react-google-maps/api";
import { useCallback, useMemo } from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";

import type { RefugeSummary } from "../api/schemas";
import { useGoogleMapsLoaded } from "../lib/googleMaps";
import { parseLineStringWkt } from "../lib/wkt";
import { colors } from "../theme/colors";

interface Props {
  routeGeometry: string;
  refuges: RefugeSummary[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

const CONTAINER_STYLE = { width: "100%", height: 320 };

// FR-09: refuge candidates plotted near the selected route on a real map
// (web only). Markers are clickable circles: "+" unselected, checkmark for
// the selected candidate - mirrors the Figma "Choose a quiet place" screen.
export function QuietPlacesGoogleMap({ routeGeometry, refuges, selectedId, onSelect }: Props) {
  const { isLoaded, loadError } = useGoogleMapsLoaded();
  // Memoized on the raw inputs (not recomputed as fresh array/object
  // literals every render): @react-google-maps/api's Polyline diffs its
  // `path` prop via the underlying google.maps.MVCArray, and a new array
  // reference on every render - even with identical values, e.g. after an
  // unrelated selectedId change - can hit it mid-update and throw
  // "Cannot read properties of undefined (reading 'setAt')".
  const points = useMemo(() => parseLineStringWkt(routeGeometry), [routeGeometry]);
  const path = useMemo(() => points.map((p) => ({ lat: p.lat, lng: p.lon })), [points]);
  const refugePositions = useMemo(
    () => refuges.map((r) => ({ lat: r.lat, lng: r.lon })),
    [refuges]
  );

  const onLoad = useCallback(
    (map: google.maps.Map) => {
      if (points.length < 2) return;
      const bounds = new google.maps.LatLngBounds();
      points.forEach((p) => bounds.extend({ lat: p.lat, lng: p.lon }));
      refugePositions.forEach((p) => bounds.extend(p));
      map.fitBounds(bounds, 40);
    },
    [points, refugePositions]
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
        <Polyline path={path} options={{ strokeColor: colors.calmLine, strokeWeight: 4 }} />
        <Marker position={path[0]} label="A" title="Origin" />
        <Marker position={path[path.length - 1]} label="B" title="Destination" />
        {refuges.map((refuge, index) => {
          const isSelected = refuge.id === selectedId;
          return (
            <Marker
              key={refuge.id}
              position={refugePositions[index]}
              title={refuge.name}
              onClick={() => onSelect(refuge.id)}
              icon={{
                path: google.maps.SymbolPath.CIRCLE,
                scale: 12,
                fillColor: isSelected ? colors.primary : colors.cardBackground,
                fillOpacity: 1,
                strokeColor: colors.primary,
                strokeWeight: 2,
              }}
              label={{
                text: isSelected ? "✓" : "+",
                color: isSelected ? "#FFFFFF" : colors.primary,
                fontWeight: "700",
              }}
            />
          );
        })}
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
