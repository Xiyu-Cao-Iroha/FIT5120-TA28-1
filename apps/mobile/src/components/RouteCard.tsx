import { Pressable, StyleSheet, Text, View } from "react-native";

import type { RouteOption } from "../api/schemas";
import { describeFreshness } from "../lib/freshness";
import { colors } from "../theme/colors";
import { SensoryBadge } from "./SensoryBadge";

interface Props {
  route: RouteOption;
  onPress: () => void;
}

// FR-07: each card shows name, duration, sensory text, recommendation
// status, explanation, and data freshness. Layout follows the Figma
// prototype's route-comparison card (name+duration row, pill, description,
// lighter caption) - recommendation is conveyed by the highlighted border
// plus the explanation text itself, not a separate chip, matching Figma.
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
        <Text style={styles.duration}>{route.duration_minutes} min</Text>
      </View>

      <SensoryBadge level={route.sensory_level} />

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
  headerRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "baseline", gap: 8 },
  name: { fontSize: 18, fontWeight: "700", color: colors.heading, flexShrink: 1 },
  duration: { fontSize: 15, fontWeight: "600", color: colors.heading },
  explanation: { fontSize: 14, color: colors.body, lineHeight: 20 },
  freshness: { fontSize: 12, color: colors.caption },
});
