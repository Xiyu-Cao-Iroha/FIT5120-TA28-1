import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

export type CrowdSensitivity = "low" | "moderate" | "high";

interface PreferenceContextValue {
  crowdSensitivity: CrowdSensitivity | null;
  setCrowdSensitivity: (value: CrowdSensitivity) => void;
}

const PreferenceContext = createContext<PreferenceContextValue | undefined>(undefined);

// US 1.3 (prototype-only): the selected preference is client state shared
// across Setup -> Destination -> Results, never persisted server-side
// (section 8.4: temporary interface values stay local client state).
export function PreferenceProvider({ children }: { children: ReactNode }) {
  const [crowdSensitivity, setCrowdSensitivity] = useState<CrowdSensitivity | null>(null);

  const value = useMemo(() => ({ crowdSensitivity, setCrowdSensitivity }), [crowdSensitivity]);

  return <PreferenceContext.Provider value={value}>{children}</PreferenceContext.Provider>;
}

export function usePreference(): PreferenceContextValue {
  const ctx = useContext(PreferenceContext);
  if (!ctx) throw new Error("usePreference must be used within a PreferenceProvider");
  return ctx;
}
