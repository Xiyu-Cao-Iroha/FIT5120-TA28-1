import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

/** What the user picks, in the UI's own wording: how much sensory
 *  stimulation they are comfortable with. */
export type SensoryTolerance = "low" | "moderate" | "high";

/** What the backend's /routes/compare accepts. */
export type CrowdSensitivity = "low" | "moderate" | "high";

// Tolerance and sensitivity are inverses, and both use the words low/moderate/
// high - so mapping them across straight through would silently invert the
// feature. Someone with LOW tolerance for crowds ("I prefer calmer routes")
// needs the HIGH-sensitivity threshold, which flags more routes as busy.
const CROWD_SENSITIVITY_BY_TOLERANCE: Record<SensoryTolerance, CrowdSensitivity> = {
  low: "high",
  moderate: "moderate",
  high: "low",
};

interface PreferenceContextValue {
  sensoryTolerance: SensoryTolerance | null;
  setSensoryTolerance: (value: SensoryTolerance) => void;
  /** Derived from sensoryTolerance - send this to the API, never the raw
   *  tolerance value. */
  crowdSensitivity: CrowdSensitivity | null;
}

const PreferenceContext = createContext<PreferenceContextValue | undefined>(undefined);

// US 1.3 (prototype-only): the selected preference is client state shared
// across Home -> Results, never persisted server-side (section 8.4:
// temporary interface values stay local client state).
export function PreferenceProvider({ children }: { children: ReactNode }) {
  const [sensoryTolerance, setSensoryTolerance] = useState<SensoryTolerance | null>(null);

  const value = useMemo(
    () => ({
      sensoryTolerance,
      setSensoryTolerance,
      crowdSensitivity: sensoryTolerance ? CROWD_SENSITIVITY_BY_TOLERANCE[sensoryTolerance] : null,
    }),
    [sensoryTolerance]
  );

  return <PreferenceContext.Provider value={value}>{children}</PreferenceContext.Provider>;
}

export function usePreference(): PreferenceContextValue {
  const ctx = useContext(PreferenceContext);
  if (!ctx) throw new Error("usePreference must be used within a PreferenceProvider");
  return ctx;
}
