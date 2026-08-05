interface DemoScenario {
  key: string;
  label: string;
  origin: { lat: number; lon: number; label: string };
  destination: { lat: number; lon: number; label: string };
}

// Matches services/api/app/seed.py's DEMO_SCENARIOS one-for-one, so each
// button here has pedestrian data seeded and ready to compare against
// locally. Keep both lists in sync when adding/removing a scenario.
export const DEMO_SCENARIOS: DemoScenario[] = [
  {
    key: "southern-cross-state-library",
    label: "Low vs High sensory",
    origin: { lat: -37.8183, lon: 144.9531, label: "Southern Cross Station" },
    destination: { lat: -37.8095, lon: 144.9646, label: "State Library Victoria" },
  },
  {
    key: "market-flinders",
    label: "All routes congested",
    origin: { lat: -37.8076, lon: 144.9568, label: "Queen Victoria Market" },
    destination: { lat: -37.8183, lon: 144.9671, label: "Flinders Street Station" },
  },
  {
    key: "flinders-qv-market",
    label: "One route unavailable",
    origin: { lat: -37.8183, lon: 144.9671, label: "Flinders Street Station" },
    destination: { lat: -37.8076, lon: 144.9568, label: "Queen Victoria Market" },
  },
  {
    key: "state-library-market",
    label: "Low vs High, near quiet places",
    origin: { lat: -37.8095, lon: 144.9646, label: "State Library Victoria" },
    destination: { lat: -37.8076, lon: 144.9568, label: "Queen Victoria Market" },
  },
];
