import { useLocalSearchParams, useRouter } from "expo-router";
import { useMemo } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import { useRouteComparison } from "../src/api/queries";
import { BackLink } from "../src/components/BackLink";
import { RouteCard } from "../src/components/RouteCard";
import { describeApiError } from "../src/lib/errors";
import { usePreference } from "../src/state/preference";
import { colors } from "../src/theme/colors";

// FR-07 + section 7: route comparison results with loading, error, empty,
// unavailable-data and all-congested states each explicitly handled.
// Layout follows the Figma "Choose a calmer route" screen.
export default function RouteResultsScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{
    originLat: string;
    originLon: string;
    destinationLat: string;
    destinationLon: string;
  }>();

  const origin = useMemo(
    () => ({ lat: Number(params.originLat), lon: Number(params.originLon) }),
    [params.originLat, params.originLon]
  );
  const destination = useMemo(
    () => ({ lat: Number(params.destinationLat), lon: Number(params.destinationLon) }),
    [params.destinationLat, params.destinationLon]
  );

  const { crowdSensitivity, sensoryTolerance } = usePreference();
  const { data, error, isPending, isFetching, refetch } = useRouteComparison(origin, destination, crowdSensitivity);

  const goEditDestination = () => router.back();

  if (isPending) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color={colors.primary} accessibilityLabel="Comparing routes" />
        <Text style={styles.loadingText}>Comparing routes for pedestrian congestion...</Text>
      </View>
    );
  }

  if (error) {
    const { title, message, action } = describeApiError(error);
    return (
      <View style={styles.centered}>
        <Text style={styles.errorTitle}>{title}</Text>
        <Text style={styles.errorBody}>{message}</Text>
        <View style={styles.actionsRow}>
          <Pressable
            style={styles.secondaryButton}
            onPress={goEditDestination}
            accessibilityRole="button"
            accessibilityLabel="Edit destination"
          >
            <Text style={styles.secondaryButtonText}>Edit destination</Text>
          </Pressable>
          {action === "retry" ? (
            <Pressable
              style={[styles.primaryButton, isFetching && styles.disabledButton]}
              onPress={() => !isFetching && refetch()}
              disabled={isFetching}
              accessibilityRole="button"
              accessibilityLabel="Retry comparison"
              accessibilityState={{ disabled: isFetching, busy: isFetching }}
            >
              <Text style={styles.primaryButtonText}>{isFetching ? "Retrying..." : "Retry"}</Text>
            </Pressable>
          ) : null}
        </View>
      </View>
    );
  }

  if (!data || data.routes.length === 0) {
    return (
      <View style={styles.centered}>
        <Text style={styles.errorTitle}>No walking route found</Text>
        <Text style={styles.errorBody}>
          We couldn't find a walking route between these two points. Try a different origin or destination.
        </Text>
        <Pressable
          style={styles.primaryButton}
          onPress={goEditDestination}
          accessibilityRole="button"
          accessibilityLabel="Change origin or destination"
        >
          <Text style={styles.primaryButtonText}>Change origin or destination</Text>
        </Pressable>
      </View>
    );
  }

  const allCongested = data.routes.every((r) => r.sensory_level === "high");
  const recommended = data.routes.find((r) => r.is_recommended);

  // Figma's recommended-route caption references the user's own preference
  // directly when one is set and the routes aren't all congested; otherwise
  // fall back to the backend's own congestion-based explanation. This quotes
  // the tolerance wording the user actually chose, not the inverted
  // crowd-sensitivity value sent to the API (see src/state/preference.tsx).
  const displayRoutes = data.routes.map((route) => {
    if (route.is_recommended && !allCongested && sensoryTolerance) {
      return { ...route, explanation: `Recommended for your ${sensoryTolerance} sensory tolerance preference.` };
    }
    return route;
  });

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <BackLink label="Search" onPress={goEditDestination} />
      <Text style={styles.title}>{allCongested ? "Routes have some congestion" : "Choose a calmer route"}</Text>
      <Text style={styles.subtitle}>
        {allCongested
          ? "Compare the available routes and choose the option with comparatively lower pedestrian congestion."
          : "Sensory levels use available pedestrian congestion information and are shown with text labels."}
      </Text>

      {allCongested ? (
        <View style={styles.noticeBanner}>
          <Text style={styles.noticeText}>All available routes currently contain some congestion.</Text>
        </View>
      ) : null}

      {displayRoutes.map((route) => (
        <RouteCard
          key={route.id}
          route={route}
          onPress={() => router.push({ pathname: "/route-map/[routeId]", params: { routeId: route.id } })}
        />
      ))}

      <Text style={styles.footerCaption}>
        {allCongested && recommended
          ? `${recommended.name} is recommended for comparison; it is not congestion-free.`
          : "Tap a route to view congested segments."}
      </Text>
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
  loadingText: { fontSize: 15, color: colors.body, textAlign: "center" },
  title: { fontSize: 22, fontWeight: "700", color: colors.heading },
  subtitle: { fontSize: 14, color: colors.body, lineHeight: 20, marginBottom: 4 },
  errorTitle: { fontSize: 18, fontWeight: "700", color: colors.heading, textAlign: "center" },
  errorBody: { fontSize: 15, color: colors.body, textAlign: "center" },
  noticeBanner: {
    backgroundColor: colors.noticeAmberBg,
    borderColor: colors.noticeAmberBorder,
    borderWidth: 1,
    borderRadius: 10,
    padding: 14,
  },
  noticeText: { fontSize: 13, color: colors.noticeAmberText, fontWeight: "500" },
  footerCaption: { fontSize: 13, color: colors.caption, textAlign: "center", marginTop: 4 },
  actionsRow: { flexDirection: "row", gap: 12, marginTop: 8 },
  primaryButton: {
    backgroundColor: colors.primary,
    borderRadius: 10,
    paddingHorizontal: 20,
    paddingVertical: 12,
    minHeight: 44,
    alignItems: "center",
    justifyContent: "center",
  },
  primaryButtonText: { color: "white", fontWeight: "700" },
  secondaryButton: {
    borderWidth: 1,
    borderColor: colors.primary,
    borderRadius: 10,
    paddingHorizontal: 20,
    paddingVertical: 12,
    minHeight: 44,
    alignItems: "center",
    justifyContent: "center",
  },
  secondaryButtonText: { color: colors.primary, fontWeight: "700" },
  disabledButton: { opacity: 0.6 },
});
