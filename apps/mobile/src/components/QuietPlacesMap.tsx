import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import Svg, { Circle, Line } from "react-native-svg";

import type { RefugeSummary } from "../api/schemas";
import { parseLineStringWkt } from "../lib/wkt";
import { colors } from "../theme/colors";

interface Props {
  routeGeometry: string;
  refuges: RefugeSummary[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

const WIDTH = 320;
const HEIGHT = 320;
const PADDING = 32;
const GRID_LINES = 4;

// FR-09: refuge candidates plotted near the selected route, matching the
// Figma "Choose a quiet place" screen (+ marker -> checkmark on selection).
// Markers are real Pressable views layered over the SVG rather than SVG
// onPress handlers, since RN Web's SVG touch handling is inconsistent.
export function QuietPlacesMap({ routeGeometry, refuges, selectedId, onSelect }: Props) {
  const points = parseLineStringWkt(routeGeometry);
  if (points.length < 2) return null;

  const allLats = [...points.map((p) => p.lat), ...refuges.map((r) => r.lat)];
  const allLons = [...points.map((p) => p.lon), ...refuges.map((r) => r.lon)];
  const minLat = Math.min(...allLats);
  const maxLat = Math.max(...allLats);
  const minLon = Math.min(...allLons);
  const maxLon = Math.max(...allLons);
  const latRange = maxLat - minLat || 0.0001;
  const lonRange = maxLon - minLon || 0.0001;

  const toXY = (lat: number, lon: number) => {
    const x = PADDING + ((lon - minLon) / lonRange) * (WIDTH - PADDING * 2);
    const y = HEIGHT - PADDING - ((lat - minLat) / latRange) * (HEIGHT - PADDING * 2);
    return { x, y };
  };

  const start = toXY(points[0].lat, points[0].lon);
  const end = toXY(points[points.length - 1].lat, points[points.length - 1].lon);

  return (
    <View style={styles.container}>
      <Svg
        width={WIDTH}
        height={HEIGHT}
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        accessibilityLabel="Map of your route with nearby quiet place markers"
      >
        {Array.from({ length: GRID_LINES }).map((_, i) => {
          const t = (i + 1) / (GRID_LINES + 1);
          const x = PADDING + t * (WIDTH - PADDING * 2);
          const y = PADDING + t * (HEIGHT - PADDING * 2);
          return (
            <React.Fragment key={i}>
              <Line x1={x} y1={0} x2={x} y2={HEIGHT} stroke={colors.gridLine} strokeWidth={1} />
              <Line x1={0} y1={y} x2={WIDTH} y2={y} stroke={colors.gridLine} strokeWidth={1} />
            </React.Fragment>
          );
        })}
        {points.slice(0, -1).map((point, index) => {
          const next = points[index + 1];
          const a = toXY(point.lat, point.lon);
          const b = toXY(next.lat, next.lon);
          return (
            <Line
              key={index}
              x1={a.x}
              y1={a.y}
              x2={b.x}
              y2={b.y}
              stroke={colors.calmLine}
              strokeWidth={4}
              strokeLinecap="round"
            />
          );
        })}
        <Circle cx={start.x} cy={start.y} r={7} fill={colors.primary} />
        <Circle cx={end.x} cy={end.y} r={7} fill={colors.heading} />
      </Svg>

      {refuges.map((refuge) => {
        const { x, y } = toXY(refuge.lat, refuge.lon);
        const isSelected = refuge.id === selectedId;
        return (
          <Pressable
            key={refuge.id}
            style={[styles.marker, { left: x - 16, top: y - 16 }, isSelected && styles.markerSelected]}
            onPress={() => onSelect(refuge.id)}
            accessibilityRole="button"
            accessibilityLabel={`${refuge.name}${isSelected ? ", selected" : ""}`}
            accessibilityState={{ selected: isSelected }}
          >
            <Text style={[styles.markerText, isSelected && styles.markerTextSelected]}>{isSelected ? "✓" : "+"}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: WIDTH,
    height: HEIGHT,
    alignSelf: "center",
    backgroundColor: colors.cardBackground,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  marker: {
    position: "absolute",
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: colors.cardBackground,
    borderWidth: 2,
    borderColor: colors.primary,
    alignItems: "center",
    justifyContent: "center",
  },
  markerSelected: { backgroundColor: colors.primary },
  markerText: { color: colors.primary, fontWeight: "700", fontSize: 16 },
  markerTextSelected: { color: "white" },
});
