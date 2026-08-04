# CalmPath Development Requirements — Condensed (Frontend / Backend)

> Condensed from `CalmPath_App_Development_Requirements.md`. Keeps only implementation-relevant content; drops background, personas, business scoping rationale, and risk lists.

Stack: **React Native (Expo) + FastAPI + PostgreSQL/PostGIS**

---

## 1. Frontend (React Native / Expo)

### 1.1 Tech choices

- React Native with TypeScript
- Expo (build/dev platform)
- Expo Router (navigation)
- TanStack Query or equivalent (server state)
- Zod or equivalent (client-side response validation)
- OpenAPI-generated client types where practical

### 1.2 Screens

| Screen | Purpose | Scope |
|---|---|---|
| `PreferenceSetupScreen` | Select low/moderate/high crowd sensitivity | Prototype only unless US 1.3 is promoted |
| `DestinationScreen` | Select origin and destination | MVP |
| `RouteResultsScreen` | Compare routes, labels, duration, explanations | MVP |
| `RouteMapScreen` | View route and congested segments | MVP |
| `QuietPlacesScreen` | Select a nearby refuge candidate | Stretch |
| `QuietPlaceDetailScreen` | View place details and route to it | Stretch |

### 1.3 Form and interaction (maps to FR-01)

- User must be able to select or enter an origin and destination — coordinates or a controlled place identifier.
- Destination must be validated against the configured CBD service boundary.
- Both client and backend must validate input.
- On validation failure, show a field-level error **without clearing the user's existing input**.
- Submit button must show a loading state and prevent duplicate submissions.

### 1.4 Route results display (maps to FR-07)

Each route card must show:

- Route name
- Estimated duration
- Distance, where useful
- `Low Sensory` / `High Sensory` / `Sensory information unavailable` text
- Recommendation status
- A short explanation
- Freshness/update time of the pedestrian data

### 1.5 Route map and details (maps to FR-08)

- Display selected route, origin, and destination.
- Congested segments must be identifiable on the map.
- Equivalent information must also be available as text (**map must not be the only source of truth**).
- User can return to the route comparison screen.

### 1.6 Display rules (hard constraints that directly affect UI implementation)

- Sensory level **must be communicated via text**; color/icons are supporting cues only, never red/green alone.
- When data is insufficient, show `Sensory information unavailable` — never guess a level.
- When all routes are congested, explicitly state the recommended route is not congestion-free.

### 1.7 Accessibility

- Interactive targets at least 44×44 points.
- Support dynamic text sizing without clipping critical content.
- Text/background contrast must meet WCAG 2.1 AA.
- Every icon, route label, map marker, and action needs an accessible label.
- Focus order must follow visual reading order.
- Respect the user's reduced-motion preference.
- Avoid flashing, unexpected movement, and unnecessary stimulation.
- Core flow must be usable via keyboard navigation and screen reader on supported platforms.

### 1.8 Client state

- Server responses, caching, retries, freshness → managed as server state (e.g. TanStack Query).
- Selected route, temporary UI values → local client state.
- **Do not persist exact journey history by default.**
- Rendering failures must be caught by an error boundary with a recovery action (never a blank/broken screen).

### 1.9 Error/edge states the frontend must handle

| Situation | Frontend behavior | Recovery action |
|---|---|---|
| One route has no usable data | Show `Sensory information unavailable`; no sensory-based recommendation | View another route or retry |
| All routes are congested | State that all routes contain congestion, highlight the comparatively lower one | Compare and choose a route |
| Destination invalid or outside CBD | Field-level validation error, preserve input | Edit the destination |
| Open-data service unavailable | Show data freshness / temporary-unavailability info | Use a still-valid cached snapshot or retry later |
| No walking route available | Explain no route was found | Change origin or destination |
| No refuge location nearby | Show empty state, never invent a location | Expand search or return to route |

### 1.10 Frontend test requirements

- Cover loading / success / empty / unavailable-data / retry states.
- Verify sensory text is present and not color-dependent.
- Recommendation and explanation content matches the API response.
- Keyboard focus order and screen-reader labels.
- Large text, reduced motion, color-blindness simulation, weak-network behavior.
- Duplicate submissions are blocked.
- Toolchain: ESLint, Prettier, TypeScript, Jest, React Native Testing Library.

---

## 2. Backend (FastAPI)

### 2.1 Responsibilities

- Validate all client input with Pydantic.
- Validate the configured service boundary (CBD).
- Orchestrate: routing provider, pedestrian-data repository, classification rules, recommendation explanation.
- Expose a stable, versioned REST API.
- Run/coordinate scheduled open-data synchronization.
- Provide structured logs, health checks, metrics, OpenAPI docs.
- Never expose internal errors, SQL, credentials, or precise user location in logs.

### 2.2 API endpoints

| Method & path | Purpose | Main response |
|---|---|---|
| `GET /api/v1/health` | Liveness/readiness | API, database, and data-freshness status |
| `POST /api/v1/routes/compare` | Generate and compare candidate routes | Routes, recommendation, explanations, data snapshot |
| `GET /api/v1/routes/{route_id}` | Retrieve route details | Route segments, sensor coverage, explanation |
| `GET /api/v1/refuges` | Find refuge candidates near a route/point | Place summaries (Stretch) |
| `GET /api/v1/refuges/{place_id}` | Retrieve refuge details | Place, category, address, facilities, source (Stretch) |
| `POST /internal/data-sync` | Trigger a protected sync job | Internal only, not exposed to the public app |

### 2.3 `routes/compare` response fields (per route, minimum)

```
id, name, duration_minutes, distance_meters, geometry,
sensory_level, crowd_score (nullable when unavailable),
data_coverage, is_recommended, explanation,
congested_segments, data_updated_at, rule_version
```

### 2.4 Error contract

| HTTP status | Error code | Meaning |
|---|---|---|
| 400 | `INVALID_LOCATION` | Invalid coordinates, or origin equals destination |
| 422 | `OUTSIDE_SERVICE_AREA` | Destination outside the configured CBD boundary |
| 404 | `NO_ROUTE_FOUND` | No candidate walking route available |
| 429 | `RATE_LIMITED` | Request limit exceeded |
| 503 | `DATA_SOURCE_UNAVAILABLE` | No sufficiently fresh open-data snapshot available |
| 500 | `INTERNAL_ERROR` | Generic production error, no internal implementation details |

### 2.5 Core business logic (FR-02 through FR-06)

**Candidate route generation**
- A valid request returns at least 1 route, target of 2 for comparison.
- Routing provider must sit behind an adapter so it can be swapped without changing the client API.
- Controlled demo routes may back the MVP if no production routing provider is approved yet.
- All routes in one comparison must share the same data snapshot and classification-rule version.

**Pedestrian-data ingestion**
- Ingest City of Melbourne pedestrian sensor locations.
- Ingest the latest per-minute/per-hour pedestrian counts.
- Every imported record retains source, observation time, sync run, and quality status.
- Sync must be idempotent and safe to retry.
- An incomplete import must not replace the last successful active snapshot.

**Route-to-sensor matching**
- Candidate routes are divided into analyzable segments.
- Sensors within a configurable distance of a segment are associated with it.
- Record sensor count and data coverage used per route.
- Observations older than the configured max age must not be used for classification.
- Areas without sensor coverage must **not** default to "low sensory."

**Sensory classification (rule-based, not ML)**

| Classification | Rule |
|---|---|
| Low Sensory | Coverage meets minimum AND crowd score below configured threshold |
| High Sensory | Coverage meets minimum AND crowd score ≥ configured threshold |
| Unavailable | Insufficient, stale, or invalid pedestrian data |

Thresholds, minimum coverage, max data age, and active rule version must be stored as configuration and covered by automated tests.

**Recommendation logic**
- Recommend the valid route with the lowest crowd score.
- Response must explain why the route was recommended.
- Never recommend a shorter route solely for being faster if it has higher crowd exposure.
- If all routes are congested, identify the comparatively lower-congestion option and explicitly state it isn't congestion-free.
- A route with unavailable sensory data must not receive a sensory-based recommendation.

### 2.6 Database (PostgreSQL + PostGIS)

**Core entities**

| Table | Key fields | Purpose |
|---|---|---|
| `data_sources` | `id, name, url, licence, refresh_interval` | Open-data source registry |
| `sync_runs` | `id, source_id, timestamps, status, row_count, error` | Sync audit |
| `pedestrian_sensors` | `id, external_id, name, geom, active` | Sensor locations |
| `pedestrian_observations` | `sensor_id, observed_at, count, interval, quality_flag, sync_run_id` | Pedestrian count time series |
| `places` | `id, source ids, name, category, address, geom, metadata` | Landmarks/refuge candidates |
| `route_requests` | `id, origin, destination, snapshot, rule_version` | Optional short-lived anonymous request audit |
| `route_options` | `id, request_id, duration, distance, geom, score, level, coverage, recommended` | Route comparison result |
| `route_segments` | `id, route_id, sequence, geom, score, level, sensor_count` | Explainable segment analysis |
| `classification_rules` | `version, threshold, min_coverage, max_data_age, active` | Versioned rule config |

**Constraints and indexes**

- Unique constraint on `(sensor_id, observed_at)` in `pedestrian_observations`.
- Pedestrian counts must not be negative.
- Spatial columns use SRID 4326 unless a documented projected CRS is required.
- Spatial columns need GiST indexes.
- Index on `(sensor_id, observed_at DESC)` for observations.
- Times stored as `timestamptz` in UTC, returned as ISO 8601.
- The API database role must **not** have schema-migration privileges.
- Migrations managed through Alembic.

**Retention**

- Exact route requests/derived results should have short retention (recommended 24h) or be disabled when not required.
- Analytics should use aggregated data, not identifiable journey histories.
- Coordinates must be removed or reduced-precision in logs.

### 2.7 Security requirements

- Validate and constrain coordinates, text input, request size, and query frequency.
- Use SQLAlchemy parameterized queries.
- Configure CORS with explicit dev/prod origins.
- Enforce HTTPS in deployed environments.
- Never expose stack traces, SQL, connection strings, or provider credentials.
- Run Bandit, frontend linting, and dependency-vulnerability scans in CI.
- Block merges on unresolved high-severity findings.

### 2.8 Backend test requirements

- Classification below, equal to, and above the configured threshold.
- Data coverage immediately below and exactly at minimum.
- Observations immediately inside and outside the max-age boundary.
- Negative counts, duplicate observations, invalid timestamps, future timestamps.
- One unavailable route, all unavailable routes, all-congested routes.
- Correct recommendation when the faster route is more congested.
- Service-boundary validation.
- Rate limiting and production-safe error responses.
- Toolchain: Ruff/Flake8, Black, mypy, Pytest, database integration tests.

---

## 3. Shared frontend/backend contract points

- Frontend consumes the backend via OpenAPI-generated types; both sides run OpenAPI contract validation in CI.
- `POST /api/v1/routes/compare` is the core endpoint — its response shape (2.3) is directly rendered by `RouteResultsScreen` / `RouteMapScreen`.
- Error codes (2.4) must each be mapped by the frontend to a corresponding UI state (see 1.9).
