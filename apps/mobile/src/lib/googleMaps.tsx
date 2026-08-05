import { useJsApiLoader } from "@react-google-maps/api";
import { createContext, useContext, type ReactNode } from "react";

const GOOGLE_MAPS_API_KEY = process.env.EXPO_PUBLIC_GOOGLE_MAPS_API_KEY ?? "";

interface GoogleMapsLoadState {
  isLoaded: boolean;
  loadError: Error | undefined;
}

const GoogleMapsContext = createContext<GoogleMapsLoadState>({ isLoaded: false, loadError: undefined });

// Loads the Maps JavaScript API script exactly once for the whole app
// (mount this provider at the root layout) - mounting <LoadScript> per
// screen instead would reload/re-register the script on every navigation.
export function GoogleMapsProvider({ children }: { children: ReactNode }) {
  const { isLoaded, loadError } = useJsApiLoader({
    id: "calmpath-google-maps",
    googleMapsApiKey: GOOGLE_MAPS_API_KEY,
  });

  return <GoogleMapsContext.Provider value={{ isLoaded, loadError }}>{children}</GoogleMapsContext.Provider>;
}

export function useGoogleMapsLoaded(): GoogleMapsLoadState {
  return useContext(GoogleMapsContext);
}
