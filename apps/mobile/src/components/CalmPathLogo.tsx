import { StyleSheet, Text, View } from "react-native";
import Svg, { Circle, Path } from "react-native-svg";

import { colors } from "../theme/colors";

interface Props {
  /** Rendered size of the square logo mark; the wordmark scales with it. */
  size?: number;
}

// Brand lockup from the Figma home screen: a rounded dark-green tile holding
// a map pin with a tick, followed by the CalmPath wordmark. Drawn as vector
// rather than bundling the exported PNG so it stays crisp at every size the
// app renders it at.
export function CalmPathLogo({ size = 44 }: Props) {
  return (
    <View style={styles.row}>
      <View
        style={[styles.mark, { width: size, height: size, borderRadius: size * 0.3 }]}
        accessibilityRole="image"
        accessibilityLabel="CalmPath logo"
      >
        <Svg viewBox="0 0 24 24" width={size * 0.66} height={size * 0.66}>
          <Path
            d="M12 2.2c-4.1 0-7.4 3.3-7.4 7.4 0 5.5 7.4 12.2 7.4 12.2s7.4-6.7 7.4-12.2c0-4.1-3.3-7.4-7.4-7.4Z"
            fill="#F4F8F6"
          />
          <Circle cx={12} cy={9.4} r={4} fill="#C6DED2" />
          <Path
            d="M9.9 9.5 11.5 11.1 14.5 8.1"
            fill="none"
            stroke={colors.primary}
            strokeWidth={1.9}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </Svg>
      </View>
      <Text style={[styles.wordmark, { fontSize: size * 0.62 }]}>CalmPath</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", gap: 14 },
  mark: { backgroundColor: colors.primary, alignItems: "center", justifyContent: "center" },
  wordmark: { fontWeight: "700", color: colors.primary, letterSpacing: -0.2 },
});
