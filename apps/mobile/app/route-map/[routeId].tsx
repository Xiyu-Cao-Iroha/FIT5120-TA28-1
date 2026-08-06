import { useLocalSearchParams, useRouter } from "expo-router";
import { useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import { useRouteDetail } from "../../src/api/queries";
import type { RouteOption } from "../../src/api/schemas";
import { BackLink } from "../../src/components/BackLink";
import { RouteGoogleMap } from "../../src/components/RouteGoogleMap";
import { formatDistanceKm } from "../../src/lib/format";
import { colors } from "../../src/theme/colors";

function subtitleFor(route: RouteOption): string {
  if (route.sensory_level === "unavailable") return "Congestion data unavailable for this route.";
  return route.sensory_level === "low" ? "Lower-congestion walking route" : "Higher-congestion walking route";
}

function whyThisRouteHeading(route: RouteOption): string {
  if (route.sensory_level === "unavailable") return "Congestion data unavailable";
  if (route.is_recommended) return "Recommended for comparatively lower congestion";
  return "Higher pedestrian congestion";
}

// FR-08: selected route + congested segments identifiable on the map, with
// equivalent information always available as text below the diagram.
// Layout follows the Figma "Route Map" screen ("WHY THIS ROUTE" card etc.).
export default function RouteMapScreen() {
  const router = useRouter();
  const { routeId } = useLocalSearchParams<{ routeId: string }>();
  const { data: route, error, isPending } = useRouteDetail(routeId);
  const [segmentsExpanded, setSegmentsExpanded] = useState(false);

  const goBackToComparison = () => router.back();

  if (isPending) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color={colors.primary} accessibilityLabel="Loading route details" />
      </View>
    );
  }

  if (error || !route) {
    return (
      <View style={styles.centered}>
        <Text style={styles.errorTitle}>Route details unavailable</Text>
        <Text style={styles.errorBody}>
          This route detail could not be loaded. Please go back and re-run the comparison.
        </Text>
        <Pressable
          style={styles.primaryButton}
          onPress={goBackToComparison}
          accessibilityRole="button"
          accessibilityLabel="Back to route comparison"
        >
          <Text style={styles.primaryButtonText}>Back to comparison</Text>
        </Pressable>
      </View>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <BackLink label="Routes" onPress={goBackToComparison} />
      <Text style={styles.title}>
        {route.name} · {formatDistanceKm(route.distance_meters)} · {route.duration_minutes} min
      </Text>
      <Text style={styles.subtitle}>{subtitleFor(route)}</Text>

      <RouteGoogleMap routeGeometry={route.geometry} congestedSegments={route.congested_segments} />

      <View style={styles.whyCard}>
        <Text style={styles.whyLabel}>WHY THIS ROUTE</Text>
        <Text style={styles.whyHeading}>{whyThisRouteHeading(route)}</Text>
        <Text style={styles.whyBody}>{route.explanation}</Text>
      </View>

      {route.congested_segments.length === 0 ? (
        <>
          <Text style={styles.sectionTitle}>Congested segments (0)</Text>
          <Text style={styles.detailItem}>No highly congested segments identified on this route.</Text>
        </>
      ) : (
        <>
          <Pressable
            style={styles.collapsibleHeader}
            onPress={() => setSegmentsExpanded((expanded) => !expanded)}
            accessibilityRole="button"
            accessibilityLabel={`${segmentsExpanded ? "Hide" : "Show"} congested segment details`}
            accessibilityState={{ expanded: segmentsExpanded }}
          >
            <Text style={styles.sectionTitle}>Congested segments ({route.congested_segments.length})</Text>
            <Text style={styles.collapsibleToggle}>{segmentsExpanded ? "Hide ▲" : "Show ▼"}</Text>
          </Pressable>
          {segmentsExpanded &&
            route.congested_segments.map((segment) => (
              <Text key={segment.sequence} style={styles.detailItem}>
                Segment {segment.sequence + 1}: {segment.sensory_level === "high" ? "High Sensory" : "Low Sensory"}
                {segment.crowd_score != null ? ` (score ${segment.crowd_score.toFixed(2)})` : ""}
              </Text>
            ))}
        </>
      )}

      <Text style={styles.sectionTitle}>Route details</Text>
      <Text style={styles.detailItem}>Duration: {route.duration_minutes} min</Text>
      <Text style={styles.detailItem}>Distance: {Math.round(route.distance_meters)} m</Text>
      <Text style={styles.detailItem}>Data coverage: {Math.round(route.data_coverage * 100)}%</Text>

      <Pressable
        style={styles.primaryButton}
        onPress={() => router.push({ pathname: "/quiet-places", params: { routeId: route.id } })}
        accessibilityRole="button"
        accessibilityLabel="Show quiet places"
      >
        <Text style={styles.primaryButtonText}>Show quiet places</Text>
      </Pressable>

      <Pressable
        style={styles.secondaryButton}
        onPress={goBackToComparison}
        accessibilityRole="button"
        accessibilityLabel="Back to route comparison"
      >
        <Text style={styles.secondaryButtonText}>Back to comparison</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flexGrow: 1, padding: 24, paddingTop: 16, gap: 10, backgroundColor: colors.pageBackground },
  centered: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
    gap: 12,
    backgroundColor: colors.pageBackground,
  },
  title: { fontSize: 22, fontWeight: "700", color: colors.heading },
  subtitle: { fontSize: 14, color: colors.body, marginBottom: 6 },
  whyCard: {
    borderWidth: 1,
    borderColor: colors.cardBorder,
    borderRadius: 12,
    backgroundColor: colors.cardBackground,
    padding: 16,
    gap: 4,
    marginTop: 4,
  },
  whyLabel: { fontSize: 11, fontWeight: "700", color: colors.caption, letterSpacing: 0.6 },
  whyHeading: { fontSize: 16, fontWeight: "700", color: colors.heading },
  whyBody: { fontSize: 14, color: colors.body, lineHeight: 20 },
  sectionTitle: { fontSize: 13, fontWeight: "700", color: colors.caption, letterSpacing: 0.4, marginTop: 10 },
  detailItem: { fontSize: 14, color: colors.body, lineHeight: 20 },
  collapsibleHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    minHeight: 44,
  },
  collapsibleToggle: { fontSize: 13, fontWeight: "700", color: colors.primary },
  errorTitle: { fontSize: 18, fontWeight: "700", color: colors.heading, textAlign: "center" },
  errorBody: { fontSize: 15, color: colors.body, textAlign: "center" },
  primaryButton: {
    backgroundColor: colors.primary,
    borderRadius: 12,
    paddingHorizontal: 20,
    paddingVertical: 16,
    minHeight: 44,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 14,
  },
  primaryButtonText: { color: "white", fontWeight: "700", fontSize: 16 },
  secondaryButton: {
    borderWidth: 1,
    borderColor: colors.primary,
    borderRadius: 12,
    paddingHorizontal: 20,
    paddingVertical: 16,
    minHeight: 44,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 4,
  },
  secondaryButtonText: { color: colors.primary, fontWeight: "700", fontSize: 16 },
});
