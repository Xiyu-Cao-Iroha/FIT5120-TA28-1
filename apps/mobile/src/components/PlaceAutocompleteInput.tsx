import { useEffect, useRef, useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import { resolvePlace, searchPlaces } from "../api/client";
import { PlaceSearchResponseSchema, ResolvedPlaceSchema, type PlaceSuggestion } from "../api/schemas";
import { colors } from "../theme/colors";

interface SelectedPlace {
  lat: number;
  lon: number;
  description: string;
}

interface Props {
  label: string;
  placeholder: string;
  value: string;
  onChangeText: (text: string) => void;
  onSelectPlace: (place: SelectedPlace) => void;
  hasError?: boolean;
  accessibilityLabel: string;
}

const DEBOUNCE_MS = 300;
const MIN_QUERY_LENGTH = 2;

// FR-01: real address search backed by the backend's place-search adapter
// (Google Places when GOOGLE_MAPS_API_KEY is configured server-side, a
// small CBD gazetteer otherwise - see services/api/app/services/places_provider.py).
export function PlaceAutocompleteInput({
  label,
  placeholder,
  value,
  onChangeText,
  onSelectPlace,
  hasError,
  accessibilityLabel,
}: Props) {
  const [suggestions, setSuggestions] = useState<PlaceSuggestion[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [isResolving, setIsResolving] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  const handleChangeText = (text: string) => {
    onChangeText(text);
    if (timerRef.current) clearTimeout(timerRef.current);

    if (text.trim().length < MIN_QUERY_LENGTH) {
      setSuggestions([]);
      setIsOpen(false);
      return;
    }

    timerRef.current = setTimeout(async () => {
      setIsSearching(true);
      try {
        const raw = await searchPlaces(text);
        const parsed = PlaceSearchResponseSchema.parse(raw);
        setSuggestions(parsed.suggestions);
        setIsOpen(true);
      } catch {
        setSuggestions([]);
      } finally {
        setIsSearching(false);
      }
    }, DEBOUNCE_MS);
  };

  const handleSelect = async (suggestion: PlaceSuggestion) => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setIsOpen(false);
    setSuggestions([]);
    setIsResolving(true);
    try {
      const raw = await resolvePlace(suggestion.place_id);
      const resolved = ResolvedPlaceSchema.parse(raw);
      // Google's Place Details "formatted_address" (what /places/resolve
      // returns as description) is often just the postal-style address
      // without the place name - e.g. selecting "Southern Cross Station,
      // Melbourne VIC, Australia" resolved to "Melbourne VIC 3000,
      // Australia". The autocomplete suggestion's own description is what
      // the user actually saw and clicked, so it's the correct thing to
      // display - resolve is only needed for lat/lon.
      const description = suggestion.description || resolved.description;
      onChangeText(description);
      onSelectPlace({ lat: resolved.lat, lon: resolved.lon, description });
    } catch {
      // Leave the typed text as-is; validation on submit will catch an
      // unresolved location and show a field-level error (FR-01).
    } finally {
      setIsResolving(false);
    }
  };

  return (
    <View style={styles.wrapper}>
      <View style={[styles.fieldCard, hasError && styles.fieldCardError]}>
        <Text style={styles.fieldLabel}>{label}</Text>
        <View style={styles.inputRow}>
          <TextInput
            style={styles.fieldInput}
            placeholder={placeholder}
            placeholderTextColor={colors.placeholder}
            value={value}
            onChangeText={handleChangeText}
            onFocus={() => suggestions.length > 0 && setIsOpen(true)}
            onBlur={() => setTimeout(() => setIsOpen(false), 150)}
            accessibilityLabel={accessibilityLabel}
          />
          {isSearching || isResolving ? <ActivityIndicator size="small" color={colors.caption} /> : null}
        </View>
      </View>

      {isOpen && suggestions.length > 0 ? (
        <View style={styles.dropdown}>
          {suggestions.map((suggestion) => (
            <Pressable
              key={suggestion.place_id}
              style={styles.suggestionRow}
              onPress={() => handleSelect(suggestion)}
              accessibilityRole="button"
              accessibilityLabel={`Select ${suggestion.description}`}
            >
              <Text style={styles.suggestionText}>{suggestion.description}</Text>
            </Pressable>
          ))}
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: { position: "relative", zIndex: 10 },
  fieldCard: {
    borderWidth: 1,
    borderColor: colors.cardBorder,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: colors.cardBackground,
    gap: 4,
  },
  fieldCardError: { borderColor: colors.errorText },
  fieldLabel: { fontSize: 11, fontWeight: "700", color: colors.caption, letterSpacing: 0.6 },
  inputRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  fieldInput: { flex: 1, fontSize: 17, fontWeight: "600", color: colors.heading, minHeight: 26, padding: 0 },
  dropdown: {
    position: "absolute",
    top: "100%",
    left: 0,
    right: 0,
    marginTop: 4,
    backgroundColor: colors.cardBackground,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    borderRadius: 12,
    overflow: "hidden",
    zIndex: 20,
  },
  suggestionRow: { paddingHorizontal: 16, paddingVertical: 12, minHeight: 44, justifyContent: "center" },
  suggestionText: { fontSize: 15, color: colors.heading },
});
