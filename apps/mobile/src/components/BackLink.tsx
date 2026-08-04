import { Pressable, StyleSheet, Text } from "react-native";

import { colors } from "../theme/colors";

interface Props {
  label: string;
  onPress: () => void;
}

export function BackLink({ label, onPress }: Props) {
  return (
    <Pressable
      style={styles.container}
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={`Back to ${label}`}
      hitSlop={8}
    >
      <Text style={styles.text}>{"‹"} {label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: { alignSelf: "flex-start", paddingVertical: 8, minHeight: 44, justifyContent: "center" },
  text: { fontSize: 15, color: colors.caption, fontWeight: "500" },
});
