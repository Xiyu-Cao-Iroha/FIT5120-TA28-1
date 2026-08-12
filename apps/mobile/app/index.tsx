import { useRouter } from "expo-router";
import { useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, useWindowDimensions, View } from "react-native";
import Svg, { Path } from "react-native-svg";

import { CalmPathLogo } from "../src/components/CalmPathLogo";
import { DemoScenarioSidebar } from "../src/components/DemoScenarioSidebar";
import { HomeBackdrop } from "../src/components/HomeBackdrop";
import { PlaceAutocompleteInput } from "../src/components/PlaceAutocompleteInput";
import { SensoryToleranceModal, TOLERANCE_OPTIONS } from "../src/components/SensoryToleranceModal";
import { DEMO_SCENARIOS } from "../src/constants/config";
import { usePreference } from "../src/state/preference";
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

// Above this width the Figma "Web 16:9" composition applies: copy and card
// over the left, faded end of a full-bleed photo. Below it the photo moves
// above the copy instead, since there is no room to sit clear of it.
const WIDE_LAYOUT_MIN_WIDTH = 900;

function ChevronDownIcon() {
  return (
    <Svg viewBox="0 0 24 24" width={18} height={18}>
      <Path
        d="M7 10 12 15 17 10"
        fill="none"
        stroke={colors.primary}
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </Svg>
  );
}

// FR-01 + US 1.3: the app's single entry point - introduction, sensory
// tolerance preference and origin/destination search on one screen, following
// the team's Figma "01 Home" and "01A Sensory tolerance" designs.
export default function HomeScreen() {
  const router = useRouter();
  const { width } = useWindowDimensions();
  const isWide = width >= WIDE_LAYOUT_MIN_WIDTH;

  const { sensoryTolerance, setSensoryTolerance } = usePreference();
  const [originText, setOriginText] = useState("");
  const [destinationText, setDestinationText] = useState("");
  const [originPlace, setOriginPlace] = useState<LatLon | null>(null);
  const [destinationPlace, setDestinationPlace] = useState<LatLon | null>(null);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [toleranceModalOpen, setToleranceModalOpen] = useState(false);

  const selectedTolerance = TOLERANCE_OPTIONS.find((option) => option.value === sensoryTolerance);

  const fillDemoScenario = (scenario: (typeof DEMO_SCENARIOS)[number]) => {
    setOriginText(scenario.origin.label);
    setDestinationText(scenario.destination.label);
    setOriginPlace({ lat: scenario.origin.lat, lon: scenario.origin.lon });
    setDestinationPlace({ lat: scenario.destination.lat, lon: scenario.destination.lon });
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
    if (
      !nextErrors.origin &&
      !nextErrors.destination &&
      origin!.lat === destination!.lat &&
      origin!.lon === destination!.lon
    ) {
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

  // On wide screens the copy sits over the faded left end of a full-bleed
  // photo (the Figma composition). On narrow screens there is nowhere to put
  // text clear of the image, so the photo becomes a fixed band above the copy
  // that fades down into the page instead of sitting behind it.
  const heroContent = (
    <View style={[styles.heroInner, isWide ? styles.heroInnerWide : styles.heroInnerNarrow]}>
      <View style={styles.column}>
              <CalmPathLogo size={isWide ? 42 : 38} />

              <View style={styles.copyBlock}>
                <Text style={styles.eyebrow}>SENSORY-FRIENDLY WALKING</Text>
                <Text style={[styles.headline, isWide && styles.headlineWide]}>
                  Find a calmer way through Melbourne CBD.
                </Text>
                <Text style={styles.subheadline}>
                  Plan a route around pedestrian crowds and compare sensory conditions before you start
                  walking.
                </Text>
              </View>

              <View style={styles.searchCard}>
                <View style={[styles.locationRow, !isWide && styles.locationRowStacked]}>
                  <View
                    style={[styles.fieldBox, styles.locationField, Boolean(errors.origin) && styles.fieldBoxError]}
                  >
                    <PlaceAutocompleteInput
                      variant="embedded"
                      label="CURRENT LOCATION"
                      placeholder="e.g. Flinders Street Station"
                      value={originText}
                      onChangeText={(text) => {
                        setOriginText(text);
                        setOriginPlace(null);
                      }}
                      onSelectPlace={(place) => setOriginPlace({ lat: place.lat, lon: place.lon })}
                      accessibilityLabel="Current location"
                    />
                  </View>
                  <View
                    style={[
                      styles.fieldBox,
                      styles.locationField,
                      Boolean(errors.destination) && styles.fieldBoxError,
                    ]}
                  >
                    <PlaceAutocompleteInput
                      variant="embedded"
                      label="DESTINATION"
                      placeholder="e.g. State Library Victoria"
                      value={destinationText}
                      onChangeText={(text) => {
                        setDestinationText(text);
                        setDestinationPlace(null);
                      }}
                      onSelectPlace={(place) => setDestinationPlace({ lat: place.lat, lon: place.lon })}
                      accessibilityLabel="Destination"
                    />
                  </View>
                </View>
                {errors.origin ? <Text style={styles.errorText}>{errors.origin}</Text> : null}
                {errors.destination ? <Text style={styles.errorText}>{errors.destination}</Text> : null}

                <Pressable
                  style={[styles.fieldBox, styles.toleranceField]}
                  onPress={() => setToleranceModalOpen(true)}
                  accessibilityRole="button"
                  accessibilityLabel={
                    selectedTolerance
                      ? `Sensory tolerance: ${selectedTolerance.title}. Change it.`
                      : "Set your sensory tolerance"
                  }
                >
                  <View style={styles.toleranceTextWrap}>
                    <Text style={styles.fieldLabel}>SENSORY TOLERANCE</Text>
                    <Text style={[styles.fieldValue, !selectedTolerance && styles.fieldValuePlaceholder]}>
                      {selectedTolerance ? selectedTolerance.title : "Select your sensory tolerance"}
                    </Text>
                  </View>
                  <ChevronDownIcon />
                </Pressable>

                <Pressable
                  style={[styles.primaryButton, isSubmitting && styles.primaryButtonDisabled]}
                  onPress={handleSubmit}
                  disabled={isSubmitting}
                  accessibilityRole="button"
                  accessibilityLabel="Find sensory-friendly routes"
                  accessibilityState={{ disabled: isSubmitting, busy: isSubmitting }}
                >
                  <Text style={styles.primaryButtonText}>
                    {isSubmitting ? "Finding routes..." : "Find sensory-friendly routes"}
                  </Text>
                </Pressable>

                <Text style={styles.disclaimer}>
                  Preference data is used only to personalise this prototype experience.
                </Text>
              </View>
            </View>
    </View>
  );

  return (
    <>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {isWide ? (
          <View style={[styles.hero, styles.heroWide]}>
            <HomeBackdrop fade="horizontal" />
            {heroContent}
          </View>
        ) : (
          <>
            <View style={styles.photoBanner}>
              <HomeBackdrop fade="vertical" />
            </View>
            {heroContent}
          </>
        )}

      </ScrollView>

      <DemoScenarioSidebar onSelect={fillDemoScenario} />

      <SensoryToleranceModal
        visible={toleranceModalOpen}
        selected={sensoryTolerance}
        onSelect={setSensoryTolerance}
        onClose={() => setToleranceModalOpen(false)}
      />
    </>
  );
}

// Figma's content column is ~540px wide inside a 1213px frame, inset ~7.7%
// from the left edge; these keep that relationship at any viewport width.
const CONTENT_COLUMN_MAX_WIDTH = 560;

const styles = StyleSheet.create({
  scrollContent: { flexGrow: 1, backgroundColor: colors.homeBackground },

  hero: { position: "relative", overflow: "hidden" },
  // flexGrow lets the photo fill a taller viewport instead of ending part way
  // down and leaving a band of flat background beneath it.
  heroWide: { minHeight: 730, flexGrow: 1 },
  // Narrow-screen photo band; the backdrop's vertical fade blends its lower
  // edge into the page so the copy below starts on flat ground.
  photoBanner: { height: 240, position: "relative", overflow: "hidden" },
  heroInner: { position: "relative" },
  heroInnerWide: { paddingHorizontal: 72, paddingTop: 56, paddingBottom: 64 },
  heroInnerNarrow: { paddingHorizontal: 24, paddingTop: 8, paddingBottom: 44 },
  column: { width: "100%", maxWidth: CONTENT_COLUMN_MAX_WIDTH },

  copyBlock: { gap: 16, marginTop: 40 },
  eyebrow: { fontSize: 13, fontWeight: "700", color: colors.primary, letterSpacing: 1.2 },
  headline: { fontSize: 32, fontWeight: "800", color: "#141614", lineHeight: 38, letterSpacing: -0.6 },
  headlineWide: { fontSize: 44, lineHeight: 51, letterSpacing: -1.1 },
  subheadline: { fontSize: 16.5, color: colors.body, lineHeight: 25 },

  searchCard: {
    marginTop: 34,
    backgroundColor: colors.cardBackground,
    borderRadius: 18,
    padding: 26,
    gap: 14,
    // Matches the Figma card's soft drop shadow; elevation covers Android.
    shadowColor: "#000000",
    shadowOpacity: 0.16,
    shadowRadius: 18,
    shadowOffset: { width: 0, height: 8 },
    elevation: 6,
  },
  locationRow: { flexDirection: "row", gap: 14, zIndex: 3 },
  locationRowStacked: { flexDirection: "column" },
  locationField: { flex: 1 },
  fieldBox: {
    borderWidth: 1,
    borderColor: colors.cardBorder,
    borderRadius: 10,
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: colors.cardBackground,
  },
  fieldBoxError: { borderColor: colors.errorText },
  fieldLabel: { fontSize: 11, fontWeight: "700", color: colors.caption, letterSpacing: 0.7 },
  fieldValue: { fontSize: 15.5, color: colors.heading, fontWeight: "500" },
  fieldValuePlaceholder: { color: colors.placeholder, fontWeight: "400" },

  toleranceField: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    borderColor: colors.primary,
    borderWidth: 1.5,
    backgroundColor: colors.low.bg,
    minHeight: 44,
    zIndex: 1,
  },
  toleranceTextWrap: { flex: 1, gap: 3 },

  errorText: { color: colors.errorText, fontSize: 12.5, marginTop: -6 },

  primaryButton: {
    marginTop: 6,
    backgroundColor: colors.primary,
    borderRadius: 999,
    paddingVertical: 16,
    minHeight: 44,
    alignItems: "center",
    justifyContent: "center",
  },
  primaryButtonDisabled: { opacity: 0.6 },
  primaryButtonText: { color: "#FFFFFF", fontSize: 15.5, fontWeight: "700" },
  disclaimer: { fontSize: 13, color: colors.caption, lineHeight: 19, marginTop: 2 },

});
