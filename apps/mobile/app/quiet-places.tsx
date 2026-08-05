import { useLocalSearchParams, useRouter } from "expo-router";
import { useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import { useRefuges, useRouteDetail } from "../src/api/queries";
import { BackLink } from "../src/components/BackLink";
import { QuietPlacesGoogleMap } from "../src/components/QuietPlacesGoogleMap";
import { colors } from "../src/theme/colors";

// FR-09 (US 2.1, Stretch): search for refuge candidates near the selected
// route. Layout follows the Figma "Choose a quiet place" screen, including
// the "No quiet places nearby" empty state (05D) when none are found.
export default function QuietPlacesScreen() {
  const router = useRouter();
  const { routeId } = useLocalSearchParams<{ routeId: string }>();
  const { data: route, isPending: routePending } = useRouteDetail(routeId);
  const { data: refugeData, isPending: refugesPending, error } = useRefuges(routeId);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const goBackToRoute = () => router.back();

  if (routePending || refugesPending) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color={colors.primary} accessibilityLabel="Loading quiet places" />
      </View>
    );
  }

  if (error || !route || !refugeData) {
    return (
      <View style={styles.centered}>
        <Text style={styles.errorTitle}>Quiet places unavailable</Text>
        <Text style={styles.errorBody}>Please go back and try again.</Text>
        <Pressable
          style={styles.primaryButton}
          onPress={goBackToRoute}
          accessibilityRole="button"
          accessibilityLabel="Return to route"
        >
          <Text style={styles.primaryButtonText}>Return to route</Text>
        </Pressable>
      </View>
    );
  }

  if (refugeData.refuges.length === 0) {
    return (
      <ScrollView contentContainerStyle={styles.container}>
        <BackLink label="Route" onPress={goBackToRoute} />
        <Text style={styles.title}>No quiet places nearby</Text>
        <Text style={styles.subtitle}>No nearby sensory refuge locations found.</Text>
        <QuietPlacesGoogleMap routeGeometry={route.geometry} refuges={[]} selectedId={null} onSelect={() => {}} />
        <Text style={styles.footerCaption}>Try expanding the search area or continue on your selected route.</Text>
        <Pressable
          style={styles.primaryButton}
          onPress={goBackToRoute}
          accessibilityRole="button"
          accessibilityLabel="Return to route"
        >
          <Text style={styles.primaryButtonText}>Return to route</Text>
        </Pressable>
      </ScrollView>
    );
  }

  const selected = refugeData.refuges.find((r) => r.id === selectedId) ?? null;

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <BackLink label="Route" onPress={goBackToRoute} />
      <Text style={styles.title}>Choose a quiet place</Text>
      <Text style={styles.subtitle}>Tap a + marker to select a verified sensory refuge near {route.name}.</Text>

      <QuietPlacesGoogleMap
        routeGeometry={route.geometry}
        refuges={refugeData.refuges}
        selectedId={selectedId}
        onSelect={setSelectedId}
      />

      {selected ? (
        <View style={styles.selectedBox}>
          <Text style={styles.selectedLabel}>SELECTED</Text>
          <Text style={styles.selectedName}>{selected.name}</Text>
        </View>
      ) : (
        <Text style={styles.footerCaption}>Tap a + marker to select a refuge.</Text>
      )}

      <Pressable
        style={[styles.primaryButton, !selected && styles.disabledButton]}
        onPress={() => selected && router.push({ pathname: "/quiet-place/[placeId]", params: { placeId: selected.id, routeId } })}
        disabled={!selected}
        accessibilityRole="button"
        accessibilityLabel="View refuge information"
        accessibilityState={{ disabled: !selected }}
      >
        <Text style={styles.primaryButtonText}>View refuge information</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flexGrow: 1, padding: 24, paddingTop: 16, gap: 14, backgroundColor: colors.pageBackground },
  centered: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
    gap: 12,
    backgroundColor: colors.pageBackground,
  },
  title: { fontSize: 22, fontWeight: "700", color: colors.heading },
  subtitle: { fontSize: 14, color: colors.body, lineHeight: 20 },
  footerCaption: { fontSize: 13, color: colors.caption, textAlign: "center" },
  selectedBox: {
    backgroundColor: colors.low.bg,
    borderRadius: 10,
    padding: 14,
    gap: 4,
  },
  selectedLabel: { fontSize: 11, fontWeight: "700", color: colors.caption, letterSpacing: 0.6 },
  selectedName: { fontSize: 16, fontWeight: "700", color: colors.heading },
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
  disabledButton: { opacity: 0.5 },
});
