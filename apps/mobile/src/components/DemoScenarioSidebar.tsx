import { useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import Svg, { Path } from "react-native-svg";

import { DEMO_SCENARIOS } from "../constants/config";
import { colors } from "../theme/colors";

function CloseIcon() {
  return (
    <Svg viewBox="0 0 24 24" width={14} height={14}>
      <Path d="M7 7 17 17M17 7 7 17" fill="none" stroke={colors.caption} strokeWidth={2} strokeLinecap="round" />
    </Svg>
  );
}

interface Props {
  onSelect: (scenario: (typeof DEMO_SCENARIOS)[number]) => void;
}

// Presentation aid, not part of the Figma design: the four pinned demo
// scenarios need to stay one tap away during a demo, but putting them on the
// home screen itself clutters the designed composition. Docking them in a
// tab that is collapsed by default keeps the screen faithful to the design
// while the scenarios stay reachable.
export function DemoScenarioSidebar({ onSelect }: Props) {
  const [expanded, setExpanded] = useState(false);

  if (!expanded) {
    return (
      <Pressable
        style={styles.handle}
        onPress={() => setExpanded(true)}
        accessibilityRole="button"
        accessibilityLabel="Show demo scenarios"
        accessibilityState={{ expanded: false }}
      >
        <Text style={styles.handleText}>DEMO</Text>
      </Pressable>
    );
  }

  return (
    <View style={styles.panel} accessibilityLabel="Demo scenarios">
      <View style={styles.panelHeader}>
        <Text style={styles.panelTitle}>DEMO SCENARIOS</Text>
        <Pressable
          style={styles.closeButton}
          onPress={() => setExpanded(false)}
          accessibilityRole="button"
          accessibilityLabel="Hide demo scenarios"
          accessibilityState={{ expanded: true }}
        >
          <CloseIcon />
        </Pressable>
      </View>

      <ScrollView contentContainerStyle={styles.list}>
        {DEMO_SCENARIOS.map((scenario) => (
          <Pressable
            key={scenario.key}
            style={styles.row}
            onPress={() => {
              onSelect(scenario);
              setExpanded(false);
            }}
            accessibilityRole="button"
            accessibilityLabel={`Use demo scenario: ${scenario.label}, from ${scenario.origin.label} to ${scenario.destination.label}`}
          >
            <Text style={styles.rowLabel}>{scenario.label}</Text>
            <Text style={styles.rowRoute} numberOfLines={2}>
              {scenario.origin.label} → {scenario.destination.label}
            </Text>
          </Pressable>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  handle: {
    position: "absolute",
    top: 22,
    right: 0,
    backgroundColor: colors.primary,
    borderTopLeftRadius: 10,
    borderBottomLeftRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    minHeight: 44,
    justifyContent: "center",
    shadowColor: "#000000",
    shadowOpacity: 0.18,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 3 },
    elevation: 5,
  },
  handleText: { color: "#FFFFFF", fontSize: 11, fontWeight: "700", letterSpacing: 0.9 },

  panel: {
    position: "absolute",
    top: 22,
    right: 0,
    width: 250,
    maxHeight: 340,
    backgroundColor: colors.cardBackground,
    borderTopLeftRadius: 14,
    borderBottomLeftRadius: 14,
    borderWidth: 1,
    borderRightWidth: 0,
    borderColor: colors.cardBorder,
    paddingVertical: 12,
    paddingHorizontal: 14,
    shadowColor: "#000000",
    shadowOpacity: 0.16,
    shadowRadius: 16,
    shadowOffset: { width: 0, height: 6 },
    elevation: 6,
  },
  panelHeader: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 8 },
  panelTitle: { fontSize: 10.5, fontWeight: "700", color: colors.caption, letterSpacing: 0.9 },
  closeButton: {
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.pageBackground,
  },

  list: { gap: 7 },
  row: {
    borderWidth: 1,
    borderColor: colors.cardBorder,
    borderRadius: 9,
    paddingHorizontal: 11,
    paddingVertical: 8,
    minHeight: 44,
    justifyContent: "center",
    backgroundColor: colors.cardBackground,
  },
  rowLabel: { fontSize: 12.5, fontWeight: "600", color: colors.primary },
  rowRoute: { fontSize: 10.5, color: colors.caption, marginTop: 2, lineHeight: 14 },
});
