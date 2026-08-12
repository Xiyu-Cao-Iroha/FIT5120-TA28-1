import { Image, StyleSheet, View } from "react-native";
import Svg, { Defs, LinearGradient, Rect, Stop } from "react-native-svg";

import { colors } from "../theme/colors";

// The Melbourne CBD streetscape behind the home screen. In the Figma the photo
// is full-bleed across the whole frame and is faded out towards the left by a
// wash in the page background colour, so the headline and card sit on flat
// light ground while the right-hand side is pure photo - it is one continuous
// image, not a hard split down the middle.
const HERO_PHOTO = require("../../assets/home-hero.png");

interface Props {
  /** "horizontal" reproduces the Figma fade (opaque left -> clear right).
   *  "vertical" is the narrow-screen adaptation: the photo sits above the
   *  copy and fades down into the page rather than behind it, which keeps
   *  text legible when there is no room to place it clear of the image. */
  fade: "horizontal" | "vertical";
}

// offset -> opacity of the page-background wash laid over the photo.
const HORIZONTAL_STOPS: [string, number][] = [
  ["0", 1],
  ["0.3", 1],
  ["0.44", 0.92],
  ["0.56", 0.4],
  ["0.68", 0],
];
const VERTICAL_STOPS: [string, number][] = [
  ["0", 0],
  ["0.45", 0],
  ["0.8", 0.72],
  ["1", 1],
];

export function HomeBackdrop({ fade }: Props) {
  const isHorizontal = fade === "horizontal";
  const stops = isHorizontal ? HORIZONTAL_STOPS : VERTICAL_STOPS;

  return (
    <View style={styles.fill} pointerEvents="none">
      <Image
        source={HERO_PHOTO}
        style={styles.photo}
        resizeMode="cover"
        accessibilityIgnoresInvertColors
        // Purely decorative: the heading and copy already carry the meaning,
        // so announcing it would only add noise for screen readers.
        accessible={false}
        alt=""
      />
      <View style={styles.overlay}>
        <Svg width="100%" height="100%" viewBox="0 0 100 100" preserveAspectRatio="none">
          <Defs>
            <LinearGradient
              id="heroFade"
              x1="0"
              y1="0"
              x2={isHorizontal ? "1" : "0"}
              y2={isHorizontal ? "0" : "1"}
            >
              {stops.map(([offset, opacity]) => (
                <Stop key={offset} offset={offset} stopColor={colors.homeBackground} stopOpacity={opacity} />
              ))}
            </LinearGradient>
          </Defs>
          <Rect x="0" y="0" width="100" height="100" fill="url(#heroFade)" />
        </Svg>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  fill: { position: "absolute", top: 0, left: 0, right: 0, bottom: 0 },
  photo: { position: "absolute", top: 0, left: 0, right: 0, bottom: 0, width: "100%", height: "100%" },
  overlay: { position: "absolute", top: 0, left: 0, right: 0, bottom: 0 },
});
