import { Modal, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import Svg, { Path } from "react-native-svg";

import type { SensoryTolerance } from "../state/preference";
import { colors } from "../theme/colors";

export const TOLERANCE_OPTIONS: { value: SensoryTolerance; title: string; description: string }[] = [
  {
    value: "low",
    title: "Low sensory tolerance",
    description: "I prefer calmer routes and want to avoid pedestrian crowds.",
  },
  {
    value: "moderate",
    title: "Moderate sensory tolerance",
    description: "Some crowd exposure is comfortable for me.",
  },
  {
    value: "high",
    title: "High sensory tolerance",
    description: "I am comfortable with busy and crowded routes.",
  },
];

function TickIcon() {
  return (
    <Svg viewBox="0 0 24 24" width={16} height={16}>
      <Path
        d="M6 12.5 10.2 16.7 18 8.9"
        fill="none"
        stroke="#FFFFFF"
        strokeWidth={2.4}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </Svg>
  );
}

function CloseIcon() {
  return (
    <Svg viewBox="0 0 24 24" width={16} height={16}>
      <Path
        d="M7 7 17 17M17 7 7 17"
        fill="none"
        stroke={colors.heading}
        strokeWidth={2}
        strokeLinecap="round"
      />
    </Svg>
  );
}

interface Props {
  visible: boolean;
  selected: SensoryTolerance | null;
  onSelect: (value: SensoryTolerance) => void;
  onClose: () => void;
}

// US 1.3, "Set sensory tolerance" screen: picking a level applies it straight
// away, so Done/close simply dismisses - there is no separate confirm step to
// get out of sync with what the card behind the modal already shows.
export function SensoryToleranceModal({ visible, selected, onSelect, onClose }: Props) {
  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <View style={styles.scrim}>
        <View style={styles.sheet}>
          <ScrollView contentContainerStyle={styles.sheetContent}>
            <View style={styles.titleRow}>
              <Text style={styles.title}>Set sensory tolerance</Text>
              <Pressable
                style={styles.closeButton}
                onPress={onClose}
                accessibilityRole="button"
                accessibilityLabel="Close sensory tolerance settings"
              >
                <CloseIcon />
              </Pressable>
            </View>
            <Text style={styles.subtitle}>How much sensory stimulation are you comfortable with?</Text>

            <View style={styles.optionList} accessibilityRole="radiogroup">
              {TOLERANCE_OPTIONS.map((option) => {
                const isSelected = selected === option.value;
                return (
                  <Pressable
                    key={option.value}
                    style={[styles.option, isSelected && styles.optionSelected]}
                    onPress={() => onSelect(option.value)}
                    accessibilityRole="radio"
                    // accessibilityState alone does not reach the DOM as
                    // aria-checked on react-native-web, which would leave the
                    // selection conveyed by colour and a tick icon only.
                    aria-checked={isSelected}
                    accessibilityState={{ checked: isSelected }}
                    accessibilityLabel={`${option.title}. ${option.description}`}
                  >
                    <View style={styles.optionText}>
                      <Text style={styles.optionTitle}>{option.title}</Text>
                      <Text style={styles.optionDescription}>{option.description}</Text>
                    </View>
                    {isSelected ? (
                      <View style={styles.tick}>
                        <TickIcon />
                      </View>
                    ) : null}
                  </Pressable>
                );
              })}
            </View>

            <Pressable
              style={styles.doneButton}
              onPress={onClose}
              accessibilityRole="button"
              accessibilityLabel="Done setting sensory tolerance"
            >
              <Text style={styles.doneButtonText}>Done</Text>
            </Pressable>
            <Text style={styles.footnote}>You can change this preference later.</Text>
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  scrim: {
    flex: 1,
    backgroundColor: "rgba(26, 29, 27, 0.45)",
    alignItems: "center",
    justifyContent: "center",
    padding: 20,
  },
  sheet: {
    width: "100%",
    maxWidth: 560,
    maxHeight: "90%",
    backgroundColor: colors.cardBackground,
    borderRadius: 22,
  },
  sheetContent: { padding: 28, gap: 14 },
  titleRow: { flexDirection: "row", alignItems: "flex-start", justifyContent: "space-between", gap: 16 },
  title: { flex: 1, fontSize: 24, fontWeight: "700", color: colors.heading },
  closeButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.pageBackground,
    alignItems: "center",
    justifyContent: "center",
  },
  subtitle: { fontSize: 15, color: colors.body, lineHeight: 21, marginTop: -6 },

  optionList: { gap: 12, marginTop: 6 },
  option: {
    flexDirection: "row",
    alignItems: "center",
    gap: 14,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    borderRadius: 14,
    paddingHorizontal: 20,
    paddingVertical: 18,
    minHeight: 44,
    backgroundColor: colors.cardBackground,
  },
  optionSelected: { borderColor: colors.primary, borderWidth: 2, backgroundColor: colors.low.bg },
  optionText: { flex: 1, gap: 6 },
  optionTitle: { fontSize: 17, fontWeight: "700", color: colors.heading },
  optionDescription: { fontSize: 14, color: colors.body, lineHeight: 20 },
  tick: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: colors.primary,
    alignItems: "center",
    justifyContent: "center",
  },

  doneButton: {
    marginTop: 8,
    backgroundColor: colors.primary,
    borderRadius: 999,
    paddingVertical: 16,
    minHeight: 44,
    alignItems: "center",
    justifyContent: "center",
  },
  doneButtonText: { color: "#FFFFFF", fontSize: 16, fontWeight: "700" },
  footnote: { fontSize: 13, color: colors.caption, textAlign: "center" },
});
