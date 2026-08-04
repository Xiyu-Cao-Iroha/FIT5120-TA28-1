import { useRouter } from "expo-router";
import { useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import { BackLink } from "../src/components/BackLink";
import { PlaceAutocompleteInput } from "../src/components/PlaceAutocompleteInput";
import { CBD_DEMO_LOCATIONS } from "../src/constants/config";
import { colors } from "../src/theme/colors";

interface FieldErrors {
  origin?: string;
  destination?: string;
}

interface LatLon {
  lat: number;
  lon: number;
}

const COORDINATE_PATTERN = /^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$/;

// FR-01: origin/destination entry backed by real place search (Google
// Places when configured server-side, a small CBD gazetteer otherwise -
// see PlaceAutocompleteInput). Field-level errors never clear the user's
// existing input, and the submit control guards against duplicate
// submissions. Layout follows the Figma "Destination" screen.
export default function DestinationScreen() {
  const router = useRouter();
  const [originText, setOriginText] = useState("");
  const [destinationText, setDestinationText] = useState("");
  const [originPlace, setOriginPlace] = useState<LatLon | null>(null);
  const [destinationPlace, setDestinationPlace] = useState<LatLon | null>(null);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fillDemoRoute = () => {
    setOriginText(CBD_DEMO_LOCATIONS.origin.label);
    setDestinationText(CBD_DEMO_LOCATIONS.destination.label);
    setOriginPlace({ lat: CBD_DEMO_LOCATIONS.origin.lat, lon: CBD_DEMO_LOCATIONS.origin.lon });
    setDestinationPlace({ lat: CBD_DEMO_LOCATIONS.destination.lat, lon: CBD_DEMO_LOCATIONS.destination.lon });
    setErrors({});
  };

  const resolveTypedText = (text: string): LatLon | null => {
    const match = text.match(COORDINATE_PATTERN);
    if (!match) return null;
    const lat = Number(match[1]);
    const lon = Number(match[2]);
    return Number.isFinite(lat) && Number.isFinite(lon) ? { lat, lon } : null;
  };

  const validate = () => {
    const nextErrors: FieldErrors = {};
    const origin = originPlace ?? (originText.trim() ? resolveTypedText(originText) : null);
    const destination = destinationPlace ?? (destinationText.trim() ? resolveTypedText(destinationText) : null);

    if (!origin) {
      nextErrors.origin = "Search for a CBD location and select it, or enter coordinates as 'lat, lon'.";
    }
    if (!destination) {
      nextErrors.destination = "Search for a CBD location and select it, or enter coordinates as 'lat, lon'.";
    }
    if (!nextErrors.origin && !nextErrors.destination && origin!.lat === destination!.lat && origin!.lon === destination!.lon) {
      nextErrors.destination = "Destination must be different from the origin.";
    }

    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return null;
    return { origin: origin as LatLon, destination: destination as LatLon };
  };

  const handleSubmit = () => {
    if (isSubmitting) return; // prevent duplicate submissions
    const parsed = validate();
    if (!parsed) return;

    setIsSubmitting(true);
    router.push({
      pathname: "/route-results",
      params: {
        originLat: String(parsed.origin.lat),
        originLon: String(parsed.origin.lon),
        destinationLat: String(parsed.destination.lat),
        destinationLon: String(parsed.destination.lon),
      },
    });
    setTimeout(() => setIsSubmitting(false), 500);
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <BackLink label="Setup" onPress={() => router.back()} />
      <Text style={styles.title}>Where would you like to go?</Text>
      <Text style={styles.subtitle}>Plan a sensory-aware walking route within Melbourne CBD.</Text>

      <PlaceAutocompleteInput
        label="CURRENT LOCATION"
        placeholder="e.g. Flinders Street Station"
        value={originText}
        onChangeText={(text) => {
          setOriginText(text);
          setOriginPlace(null);
        }}
        onSelectPlace={(place) => setOriginPlace({ lat: place.lat, lon: place.lon })}
        hasError={Boolean(errors.origin)}
        accessibilityLabel="Current location"
      />
      {errors.origin ? <Text style={styles.errorText}>{errors.origin}</Text> : null}

      <PlaceAutocompleteInput
        label="DESTINATION"
        placeholder="e.g. State Library Victoria"
        value={destinationText}
        onChangeText={(text) => {
          setDestinationText(text);
          setDestinationPlace(null);
        }}
        onSelectPlace={(place) => setDestinationPlace({ lat: place.lat, lon: place.lon })}
        hasError={Boolean(errors.destination)}
        accessibilityLabel="Destination"
      />
      {errors.destination ? <Text style={styles.errorText}>{errors.destination}</Text> : null}

      <Pressable
        style={[styles.submitButton, isSubmitting && styles.submitButtonDisabled]}
        onPress={handleSubmit}
        disabled={isSubmitting}
        accessibilityRole="button"
        accessibilityLabel="Find sensory-friendly routes"
        accessibilityState={{ disabled: isSubmitting, busy: isSubmitting }}
      >
        <Text style={styles.submitButtonText}>{isSubmitting ? "Checking..." : "Find sensory-friendly routes"}</Text>
      </Pressable>

      <Pressable
        style={styles.demoLink}
        onPress={fillDemoRoute}
        accessibilityRole="button"
        accessibilityLabel="Fill in the demo route from Flinders Street Station to State Library Victoria"
      >
        <Text style={styles.demoLinkText}>Use demo route</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flexGrow: 1, padding: 24, paddingTop: 16, gap: 14, backgroundColor: colors.pageBackground },
  title: { fontSize: 26, fontWeight: "700", color: colors.heading },
  subtitle: { fontSize: 15, color: colors.body, marginBottom: 8, lineHeight: 21 },
  errorText: { color: colors.errorText, fontSize: 13, marginTop: -8 },
  submitButton: {
    marginTop: 10,
    backgroundColor: colors.primary,
    borderRadius: 12,
    paddingVertical: 16,
    minHeight: 44,
    alignItems: "center",
    justifyContent: "center",
  },
  submitButtonDisabled: { opacity: 0.6 },
  submitButtonText: { color: "white", fontSize: 16, fontWeight: "700" },
  demoLink: { alignSelf: "center", paddingVertical: 10, minHeight: 44, justifyContent: "center" },
  demoLinkText: { color: colors.primary, fontWeight: "600", fontSize: 14 },
});
