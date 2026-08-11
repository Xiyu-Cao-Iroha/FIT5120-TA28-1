import { useLocalSearchParams, useRouter } from "expo-router";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import { useRouteDetail } from "../../src/api/queries";
import type { CongestedSegment, RouteOption } from "../../src/api/schemas";
import { BackLink } from "../../src/components/BackLink";
import { RouteGoogleMap } from "../../src/components/RouteGoogleMap";
import { formatDistanceKm } from "../../src/lib/format";
import { colors } from "../../src/theme/colors";
import { lineStringLengthMeters } from "../../src/lib/wkt";

function subtitleFor(route: RouteOption): string {
  if (route.sensory_level === "unavailable") return "Congestion data unavailable for this route.";
  return route.sensory_level === "low" ? "Lower-congestion walking route" : "Higher-congestion walking route";
}

function whyThisRouteHeading(route: RouteOption): string {
  if (route.sensory_level === "unavailable") return "Congestion data unavailable";
  if (route.is_recommended) return "Recommended for comparatively lower congestion";
  return "Higher pedestrian congestion";
}

// Segment numbers/ranges ("Segment 12", "Segments 12-33") are internal
// bookkeeping the user has no way to relate to anything they can see - the
// map already shows exactly where the congestion is via the red overlay.
// The text equivalent (FR-08) should describe congestion in terms a person
// actually reasons about: how much of the walk, and how many separate busy
// stretches, in real distance - not raw indices.
function countCongestedStretches(segments: CongestedSegment[]): number {
  let stretches = 0;
  let previousSequence: number | null = null;
  for (const segment of segments) {
    if (previousSequence === null || segment.sequence !== previousSequence + 1) {
      stretches += 1;
    }
    previousSequence = segment.sequence;
  }
  return stretches;
}

function congestionSummary(route: RouteOption): string {
  if (route.congested_segments.length === 0) {
    return "No highly congested sections identified on this route.";
  }
  const stretchCount = countCongestedStretches(route.congested_segments);
  const congestedMeters = route.congested_segments.reduce(
    (total, segment) => total + lineStringLengthMeters(segment.geometry),
    0,
  );
  const percent = Math.min(100, Math.round((congestedMeters / route.distance_meters) * 100));
  const stretchLabel = stretchCount === 1 ? "busy stretch" : "busy stretches";
  return `This route has ${stretchCount} ${stretchLabel}, covering about ${formatDistanceKm(congestedMeters)} (${percent}%) of the walk.`;
}

// FR-08: selected route + congested segments identifiable on the map, with
// equivalent information always available as text below the diagram.
// Layout follows the Figma "Route Map" screen ("WHY THIS ROUTE" card etc.).
export default function RouteMapScreen() {
  const router = useRouter();
  const { routeId } = useLocalSearchParams<{ routeId: string }>();
  const { data: route, error, isPending } = useRouteDetail(routeId);

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

      <Text style={styles.sectionTitle}>Congestion along this route</Text>
      <Text style={styles.detailItem}>{congestionSummary(route)}</Text>

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
