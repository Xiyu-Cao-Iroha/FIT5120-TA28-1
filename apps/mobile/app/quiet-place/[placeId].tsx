import { useLocalSearchParams, useRouter } from "expo-router";
import { useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import { useRefugeDetail, useRouteDetail } from "../../src/api/queries";
import { BackLink } from "../../src/components/BackLink";
import { QuietPlacesGoogleMap } from "../../src/components/QuietPlacesGoogleMap";
import { formatDistanceKm } from "../../src/lib/format";
import { colors } from "../../src/theme/colors";

const CATEGORY_LABELS: Record<string, string> = {
  library: "LIBRARY · QUIET INDOOR SPACE",
  courtyard: "COURTYARD · SHELTERED QUIET SPACE",
  museum: "MUSEUM · SHELTERED OUTDOOR SPACE",
  place_of_worship: "PLACE OF WORSHIP · QUIET INDOOR SPACE",
};

// FR-09 (US 2.1, Stretch): refuge detail with facility info and a walk CTA.
// Merges the Figma "Selected quiet place" and "Navigation" screens into one
// view; real turn-by-turn walking directions are out of scope for the MVP
// (requirements section 4.4), so "Walk to this refuge" is a terminal
// confirmation rather than fabricated navigation.
export default function QuietPlaceDetailScreen() {
  const router = useRouter();
  const { placeId, routeId } = useLocalSearchParams<{ placeId: string; routeId: string }>();
  const { data: route, isPending: routePending } = useRouteDetail(routeId);
  const { data: refuge, isPending: refugePending, error } = useRefugeDetail(placeId, routeId);
  const [confirmed, setConfirmed] = useState(false);

  const goBackToQuietPlaces = () => router.back();

  if (routePending || refugePending) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color={colors.primary} accessibilityLabel="Loading refuge details" />
      </View>
    );
  }

  if (error || !route || !refuge) {
    return (
      <View style={styles.centered}>
        <Text style={styles.errorTitle}>Refuge details unavailable</Text>
        <Text style={styles.errorBody}>Please go back and choose another quiet place.</Text>
        <Pressable
          style={styles.primaryButton}
          onPress={goBackToQuietPlaces}
          accessibilityRole="button"
          accessibilityLabel="Back to quiet places"
        >
          <Text style={styles.primaryButtonText}>Back to quiet places</Text>
        </Pressable>
      </View>
    );
  }

  const categoryLabel = CATEGORY_LABELS[refuge.category] ?? refuge.category.toUpperCase();

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <BackLink label="Quiet places" onPress={goBackToQuietPlaces} />
      <Text style={styles.title}>{refuge.name}</Text>

      <QuietPlacesGoogleMap
        routeGeometry={route.geometry}
        refuges={[refuge]}
        selectedId={refuge.id}
        onSelect={() => {}}
      />

      <View style={styles.infoCard}>
        <Text style={styles.categoryLabel}>{categoryLabel}</Text>
        <Text style={styles.walkMetrics}>
          {formatDistanceKm(refuge.walk_distance_meters)} · {refuge.walk_duration_minutes} min walk
        </Text>
        <Text style={styles.address}>{refuge.address}</Text>
        <Text style={styles.description}>{refuge.facility_info || refuge.short_description}</Text>
        <Text style={styles.sourceNote}>{refuge.source_note}</Text>
      </View>

      {confirmed ? (
        <View style={styles.confirmedBox}>
          <Text style={styles.confirmedText}>
            You're on your way to {refuge.name} ({Math.round(refuge.distance_meters)} m off your route).
          </Text>
        </View>
      ) : (
        <Pressable
          style={styles.primaryButton}
          onPress={() => setConfirmed(true)}
          accessibilityRole="button"
          accessibilityLabel="Walk to this refuge"
        >
          <Text style={styles.primaryButtonText}>Walk to this refuge</Text>
        </Pressable>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flexGrow: 1, padding: 24, paddingTop: 16, gap: 12, backgroundColor: colors.pageBackground },
  centered: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
    gap: 12,
    backgroundColor: colors.pageBackground,
  },
  title: { fontSize: 22, fontWeight: "700", color: colors.heading },
  infoCard: {
    borderWidth: 1,
    borderColor: colors.cardBorder,
    borderRadius: 12,
    backgroundColor: colors.cardBackground,
    padding: 16,
    gap: 6,
  },
  categoryLabel: { fontSize: 11, fontWeight: "700", color: colors.caption, letterSpacing: 0.6 },
  walkMetrics: { fontSize: 16, fontWeight: "700", color: colors.heading },
  address: { fontSize: 14, fontWeight: "400", color: colors.body },
  description: { fontSize: 14, color: colors.body, lineHeight: 20 },
  sourceNote: { fontSize: 12, color: colors.caption, marginTop: 4 },
  confirmedBox: {
    backgroundColor: colors.low.bg,
    borderRadius: 12,
    padding: 16,
  },
  confirmedText: { fontSize: 14, color: colors.low.text, fontWeight: "600" },
  errorTitle: { fontSize: 18, fontWeight: "700", color: colors.heading, textAlign: "center" },
  errorBody: { fontSize: 15, color: colors.body, textAlign: "center" },
  primaryButton: {
    backgroundColor: colors.primary,
    borderRadius: 12,
    paddingVertical: 16,
    minHeight: 44,
    alignItems: "center",
    justifyContent: "center",
  },
  primaryButtonText: { color: "white", fontSize: 16, fontWeight: "700" },
});
