import React from "react";
import { StyleSheet, View } from "react-native";
import Svg, { Circle, Line, Rect, Text as SvgText } from "react-native-svg";

import type { CongestedSegment, SensoryLevel } from "../api/schemas";
import { parseLineStringWkt } from "../lib/wkt";
import { colors } from "../theme/colors";

interface Props {
  routeGeometry: string;
  congestedSegments: CongestedSegment[];
  sensoryLevel: SensoryLevel;
}

const WIDTH = 320;
const HEIGHT = 320;
const PADDING = 32;
const GRID_LINES = 4;

// FR-08: congested segments must be identifiable on the map. Styled after
// the Figma prototype's schematic street-grid diagram (light grid texture,
// thick route line, dashed red for congested sections) - a non-tiled
// diagram with no basemap/API key dependency, always paired with the
// equivalent text list in RouteMapScreen.
export function RouteSvgMap({ routeGeometry, congestedSegments, sensoryLevel }: Props) {
  const points = parseLineStringWkt(routeGeometry);
  if (points.length < 2) {
    return null;
  }

  const lons = points.map((p) => p.lon);
  const lats = points.map((p) => p.lat);
  const minLon = Math.min(...lons);
  const maxLon = Math.max(...lons);
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);

  const lonRange = maxLon - minLon || 0.0001;
  const latRange = maxLat - minLat || 0.0001;

  const toXY = (lon: number, lat: number) => {
    const x = PADDING + ((lon - minLon) / lonRange) * (WIDTH - PADDING * 2);
    const y = HEIGHT - PADDING - ((lat - minLat) / latRange) * (HEIGHT - PADDING * 2);
    return { x, y };
  };

  const congestedBySequence = new Set(congestedSegments.map((s) => s.sequence));
  const start = toXY(points[0].lon, points[0].lat);
  const end = toXY(points[points.length - 1].lon, points[points.length - 1].lat);

  const midIndex = Math.floor((points.length - 1) / 2);
  const midPoint = toXY(points[midIndex].lon, points[midIndex].lat);
  const labelText = sensoryLevel === "high" ? "High" : sensoryLevel === "low" ? "Lower" : "Unavailable";

  return (
    <View style={styles.container}>
      <Svg
        width={WIDTH}
        height={HEIGHT}
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        accessibilityLabel="Schematic diagram of the selected route, with congested segments highlighted in red"
      >
        <Rect x={0} y={0} width={WIDTH} height={HEIGHT} fill={colors.cardBackground} />

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
          const a = toXY(point.lon, point.lat);
          const b = toXY(next.lon, next.lat);
          const isCongested = congestedBySequence.has(index);
          return (
            <Line
              key={index}
              x1={a.x}
              y1={a.y}
              x2={b.x}
              y2={b.y}
              stroke={isCongested ? colors.congestedLine : colors.calmLine}
              strokeWidth={isCongested ? 5 : 4}
              strokeDasharray={isCongested ? "2,5" : undefined}
              strokeLinecap="round"
            />
          );
        })}

        <Rect x={midPoint.x - 26} y={midPoint.y - 26} width={52} height={18} rx={9} fill={colors.cardBackground} opacity={0.9} />
        <SvgText x={midPoint.x} y={midPoint.y - 13} fontSize={11} fontWeight="700" fill={colors.heading} textAnchor="middle">
          {labelText}
        </SvgText>

        <Circle cx={start.x} cy={start.y} r={7} fill={colors.primary} />
        <SvgText x={start.x + 10} y={start.y + 4} fontSize={12} fill={colors.heading}>
          Origin
        </SvgText>
        <Circle cx={end.x} cy={end.y} r={7} fill={colors.heading} />
        <SvgText x={end.x + 10} y={end.y + 4} fontSize={12} fill={colors.heading}>
          Destination
        </SvgText>
      </Svg>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: "center",
    padding: 8,
    backgroundColor: colors.cardBackground,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
});
