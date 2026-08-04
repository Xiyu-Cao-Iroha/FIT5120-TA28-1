import { StyleSheet, Text, View } from "react-native";

import type { SensoryLevel } from "../api/schemas";
import { colors } from "../theme/colors";

const LABELS: Record<SensoryLevel, string> = {
  low: "Low sensory",
  high: "High sensory",
  unavailable: "Sensory information unavailable",
};

const TONES: Record<SensoryLevel, { bg: string; text: string }> = {
  low: colors.low,
  high: colors.high,
  unavailable: colors.unavailable,
};

// Product principle 3.3: sensory level must always be communicated through
// text, never through colour/background alone.
export function SensoryBadge({ level }: { level: SensoryLevel }) {
  const tone = TONES[level];
  return (
    <View style={[styles.badge, { backgroundColor: tone.bg }]}>
      <Text style={[styles.text, { color: tone.text }]}>{LABELS[level]}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: { alignSelf: "flex-start", paddingHorizontal: 12, paddingVertical: 6, borderRadius: 999 },
  text: { fontSize: 13, fontWeight: "600" },
});
