import { Pressable, StyleSheet, Text, View } from "react-native";
import Svg, { Path } from "react-native-svg";

import type { RouteOption } from "../api/schemas";
import { formatDistanceKm } from "../lib/format";
import { describeFreshness } from "../lib/freshness";
import { colors } from "../theme/colors";
import { SensoryBadge } from "./SensoryBadge";

interface Props {
  route: RouteOption;
  onPress: () => void;
}

function TickIcon() {
  return (
    <Svg viewBox="0 0 24 24" width={13} height={13}>
      <Path
        d="M5 12.5 9.5 17 19 7.5"
        fill="none"
        stroke="#FFFFFF"
        strokeWidth={2.8}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </Svg>
  );
}

// FR-07: each card shows name, duration, sensory text, recommendation
// status, explanation, and data freshness. Layout follows the Figma
// prototype's route-comparison card (name+duration row, pill, description,
// lighter caption).
//
// The recommended route carries an explicit "Recommended" pill, not just the
// highlighted border: a 2px border against a 1px one is easy to miss
// entirely, and the same product principle that keeps sensory level in text
// rather than colour alone (see SensoryBadge) applies to which route the app
// is actually putting forward.
export function RouteCard({ route, onPress }: Props) {
  const sensoryDescription =
    route.sensory_level === "unavailable" ? "sensory information unavailable" : `${route.sensory_level} sensory`;

  return (
    <Pressable
      style={[styles.card, route.is_recommended && styles.recommendedCard]}
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={`${route.name}, ${sensoryDescription}${
        route.is_recommended ? ", recommended" : ""
      }. View map and details.`}
    >
      <View style={styles.headerRow}>
        <Text style={styles.name}>{route.name}</Text>
        <View style={styles.metrics}>
          <Text style={styles.duration}>{route.duration_minutes} min</Text>
          <Text style={styles.distance}>{formatDistanceKm(route.distance_meters)}</Text>
        </View>
      </View>

      <View style={styles.badgeRow}>
        {route.is_recommended ? (
          <View style={styles.recommendedBadge}>
            <TickIcon />
            <Text style={styles.recommendedBadgeText}>Recommended</Text>
          </View>
        ) : null}
        <SensoryBadge level={route.sensory_level} />
      </View>

      <Text style={styles.explanation}>{route.explanation}</Text>
      <Text style={styles.freshness}>{describeFreshness(route.data_updated_at)}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    borderWidth: 1,
    borderColor: colors.cardBorder,
    borderRadius: 14,
    padding: 18,
    gap: 10,
    backgroundColor: colors.cardBackground,
  },
  recommendedCard: { borderColor: colors.primary, borderWidth: 2 },
  badgeRow: { flexDirection: "row", alignItems: "center", flexWrap: "wrap", gap: 8 },
  recommendedBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    backgroundColor: colors.primary,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 999,
  },
  recommendedBadgeText: { fontSize: 13, fontWeight: "700", color: "#FFFFFF" },
  headerRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start", gap: 8 },
  name: { fontSize: 18, fontWeight: "700", color: colors.heading, flexShrink: 1 },
  metrics: { alignItems: "flex-end" },
  duration: { fontSize: 15, fontWeight: "600", color: colors.heading },
  distance: { fontSize: 13, color: colors.caption },
  explanation: { fontSize: 14, color: colors.body, lineHeight: 20 },
  freshness: { fontSize: 12, color: colors.caption },
});
