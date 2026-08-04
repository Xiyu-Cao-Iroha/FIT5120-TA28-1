import { useRouter } from "expo-router";
import { useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import { usePreference, type CrowdSensitivity } from "../src/state/preference";
import { colors } from "../src/theme/colors";

const OPTIONS: { value: CrowdSensitivity; label: string }[] = [
  { value: "low", label: "Low sensitivity" },
  { value: "moderate", label: "Moderate sensitivity" },
  { value: "high", label: "High sensitivity" },
];

// US 1.3 (prototype-only, requirements section 15): lets the prototype
// demonstrate that a selected crowd-sensitivity preference is used to
// assess route suitability. Layout follows the Figma "Preference Setup"
// screen and is the new app entry point.
export default function PreferenceSetupScreen() {
  const router = useRouter();
  const { crowdSensitivity, setCrowdSensitivity } = usePreference();
  const [selected, setSelected] = useState<CrowdSensitivity | null>(crowdSensitivity);

  const handleContinue = () => {
    if (!selected) return;
    setCrowdSensitivity(selected);
    router.push("/destination");
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.eyebrow}>Setup 1 of 1</Text>
      <Text style={styles.title}>How sensitive are you to pedestrian crowds?</Text>
      <Text style={styles.subtitle}>
        We'll use this preference to explain which routes may feel calmer. You can change it later.
      </Text>

      <View style={styles.optionList}>
        {OPTIONS.map((option) => {
          const isSelected = selected === option.value;
          return (
            <Pressable
              key={option.value}
              style={[styles.option, isSelected && styles.optionSelected]}
              onPress={() => setSelected(option.value)}
              accessibilityRole="radio"
              accessibilityState={{ checked: isSelected }}
              accessibilityLabel={option.label}
            >
              <Text style={styles.optionText}>{option.label}</Text>
            </Pressable>
          );
        })}
      </View>

      <Pressable
        style={[styles.continueButton, !selected && styles.continueButtonDisabled]}
        onPress={handleContinue}
        disabled={!selected}
        accessibilityRole="button"
        accessibilityLabel="Continue"
        accessibilityState={{ disabled: !selected }}
      >
        <Text style={styles.continueButtonText}>Continue</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flexGrow: 1, padding: 24, paddingTop: 40, gap: 14, backgroundColor: colors.pageBackground },
  eyebrow: { fontSize: 12, fontWeight: "700", color: colors.caption, letterSpacing: 0.6 },
  title: { fontSize: 24, fontWeight: "700", color: colors.heading, lineHeight: 30 },
  subtitle: { fontSize: 14, color: colors.body, lineHeight: 20, marginBottom: 8 },
  optionList: { gap: 12 },
  option: {
    borderWidth: 1,
    borderColor: colors.cardBorder,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 16,
    backgroundColor: colors.cardBackground,
    minHeight: 44,
    justifyContent: "center",
  },
  optionSelected: { borderColor: colors.primary, borderWidth: 2, backgroundColor: colors.low.bg },
  optionText: { fontSize: 16, color: colors.heading, fontWeight: "500" },
  continueButton: {
    marginTop: 12,
    backgroundColor: colors.primary,
    borderRadius: 12,
    paddingVertical: 16,
    minHeight: 44,
    alignItems: "center",
    justifyContent: "center",
  },
  continueButtonDisabled: { opacity: 0.5 },
  continueButtonText: { color: "white", fontSize: 16, fontWeight: "700" },
});
