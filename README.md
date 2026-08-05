# CalmPath

Sensory-aware walking-route comparison for Melbourne CBD commuters. Instead of optimising only for travel time, CalmPath compares candidate walking routes by pedestrian congestion and recommends the comparatively calmer option, with a plain-text explanation.

FIT5120 TA28 team project ("Sensory-Friendly Urban Futures").

## Status

This build implements the full Figma prototype flow:

- **US 1.1** — sensory indicator (`Low Sensory` / `High Sensory` / `Sensory information unavailable`) per route
- **US 1.2** — identify and avoid highly congested pedestrian corridors, with a comparatively-lower-congestion recommendation
- **US 1.3** (prototype-only) — a selected crowd-sensitivity preference (Low/Moderate/High) scales the classification threshold for that request and is reflected in the recommended route's caption
- **US 2.1** (Stretch) — nearby sensory refuge ("quiet place") candidates near the selected route, with detail + a terminal "walk to this refuge" confirmation

Next-hour crowd prediction (US 2.2) is explicitly **not** implemented — it's out of scope for this iteration (no ML/AI), see requirements section 4.2. See [`CalmPath_App_Development_Requirements.md`](CalmPath_App_Development_Requirements.md) sections 4 and 19–20 for the full scope decision and open items.

Routing and address search now support **Google Maps Platform** (Directions API + Places API) as a real production backend, isolated behind the existing `RoutingProvider`/`PlacesProvider` adapters — set `GOOGLE_MAPS_API_KEY` in `services/api/.env` to switch both over with no other code change. Leave it unset and the app falls back to the demo routing provider and a small CBD gazetteer, so it still runs end-to-end without any API key. See "Environment variables" below.

The route map, quiet-places, and quiet-place-detail screens also render a **real Google Map** (web, via `@react-google-maps/api`) instead of the earlier schematic SVG diagram — congested segments are drawn as a red overlay polyline, and refuge candidates are clickable pin markers. This needs its own client-visible key (`EXPO_PUBLIC_GOOGLE_MAPS_API_KEY` in `apps/mobile/.env`) with **Maps JavaScript API** enabled in Google Cloud Console (a separate API from Directions/Places) — see "Environment variables" below for the security note on why this key is necessarily public.

The pedestrian data source itself is still seeded demo data until the City of Melbourne open-data ingestion pipeline is confirmed with the teaching team. Refuge candidates are similarly seeded demo data (one, State Library Victoria, mirrors a real public location; the other two are prototype placeholders — each is labelled with its actual data source in the UI, per product principle 14.2).

## Tech stack

| Layer | Stack |
|---|---|
| Mobile app | React Native (Expo, TypeScript), Expo Router, TanStack Query, Zod, react-native-svg |
| Backend API | FastAPI, SQLAlchemy 2.0, GeoAlchemy2, Alembic, Pydantic |
| Database | PostgreSQL + PostGIS (via Docker) |

## Repository structure

```text
apps/
  mobile/              # Expo React Native app
services/
  api/                 # FastAPI service
infra/
  docker-compose.yml   # Local Postgres/PostGIS
```

Documentation:

- [`CalmPath_App_Development_Requirements.md`](CalmPath_App_Development_Requirements.md) — full development baseline (requirements, API contract, DB schema, acceptance criteria, test plan)
- [`CalmPath_Dev_Requirements_FE_BE.md`](CalmPath_Dev_Requirements_FE_BE.md) / [`_EN.md`](CalmPath_Dev_Requirements_FE_BE_EN.md) — condensed frontend/backend-only reference (Chinese / English)

## Git workflow

Two long-lived branches: `main` (stable, always in a working/demo-able state) and `develop` (day-to-day work). Do feature work on `develop`, commit there, and only merge into `main` when the app is in a state you'd be happy demoing or handing in. CI runs on pushes/PRs to both.

## Prerequisites

- Python 3.11+ (tested with 3.13)
- Node.js 18+ and npm
- Docker Desktop (for Postgres/PostGIS)

## One-command dev startup

Once you've done the one-time setup below at least once (`.venv` created, `npm install` run, both `.env` files in place), `scripts/dev-start.ps1` starts everything for you: Postgres (docker compose), the backend (uvicorn on :8010, in its own window), and the frontend (Expo web on :8081, in its own window). It's safe to re-run — it checks each port first and skips anything already running instead of starting a duplicate.

```powershell
./scripts/dev-start.ps1
```

Each server keeps running in its own PowerShell window; close that window (or Ctrl+C inside it) to stop it.

## Backend setup (`services/api`)

```bash
cd services/api
py -m venv .venv
./.venv/Scripts/pip install -r requirements-dev.txt   # Windows
# source .venv/bin/activate && pip install -r requirements-dev.txt   # macOS/Linux

cp .env.example .env
```

Start the database:

```bash
cd ../../infra
docker compose up -d
```

Run migrations and seed demo data:

```bash
cd ../services/api
./.venv/Scripts/python -m alembic upgrade head
./.venv/Scripts/python -m app.seed
```

> Seed data expires after `max_observation_age_minutes` (default 30). If routes start showing `Sensory information unavailable` again, refresh it:
> ```bash
> docker exec <postgres-container> psql -U calmpath -d calmpath -c "TRUNCATE pedestrian_observations, pedestrian_sensors CASCADE;"
> ./.venv/Scripts/python -m app.seed
> ```

Run the API:

```bash
./.venv/Scripts/python -m uvicorn app.main:app --reload --port 8010
```

> **Windows note:** port 8000 (FastAPI/uvicorn's usual default) can fall inside Windows' TCP excluded-port range (`netsh interface ipv4 show excludedportrange protocol=tcp`), so this project standardises on **8010** instead — `apps/mobile/.env.example`'s `EXPO_PUBLIC_API_BASE_URL` already points there. If 8010 also happens to be excluded on your machine, pick another free port and update `EXPO_PUBLIC_API_BASE_URL` in `apps/mobile/.env` to match.
>
> `--reload` (via WatchFiles) has occasionally missed rapid successive edits on Windows in testing. If the server seems to be serving stale code after a save, stop it and start it again without relying on the reload.

API docs: `http://localhost:8010/docs`. Health check: `GET /api/v1/health`.

### Backend tests

```bash
docker exec <postgres-container> psql -U calmpath -d calmpath -c "CREATE DATABASE calmpath_test;"
./.venv/Scripts/python -m pytest
```

## Frontend setup (`apps/mobile`)

```bash
cd apps/mobile
npm install
cp .env.example .env   # point EXPO_PUBLIC_API_BASE_URL at your running API
npm run web             # or: npm run android / npm run ios
```

The app opens on a Preference Setup screen (crowd-sensitivity choice) before Destination. DestinationScreen has a **"Demo scenarios"** section with 4 buttons, each filling in a seeded origin/destination pair matching `app/seed.py`'s `DEMO_SCENARIOS`, so you can try the full journey without geocoding: a Low vs High contrast, an all-routes-congested state, a one-route-unavailable state, and a second Low vs High pair near the refuge candidates. From the route map screen, "Show quiet places" opens the refuge-selection flow.

Each demo pair's exact route geometry (from whichever provider is live at seed time) is pinned in `services/api/demo_route_cache.json` and replayed on every later request for that same pair — see "Demo scenario reliability" below for why.

### Frontend checks

```bash
npx tsc --noEmit
```

## Environment variables

| File | Variable | Purpose |
|---|---|---|
| `services/api/.env` | `DATABASE_URL` | Postgres connection string |
| `services/api/.env` | `CORS_ORIGINS` | Allowed origins for the mobile app (dev server) |
| `services/api/.env` | `CBD_MIN_LAT` / `CBD_MAX_LAT` / `CBD_MIN_LON` / `CBD_MAX_LON` | Melbourne CBD service-boundary bounding box (placeholder pending formal confirmation) |
| `services/api/.env` | `GOOGLE_MAPS_API_KEY` | Optional. Set to enable real walking routes (Directions API) and real address search (Places API). Needs both APIs enabled on the key's Google Cloud project. Leave blank to use the demo provider/gazetteer. Server-side only, never sent to the browser. |
| `apps/mobile/.env` | `EXPO_PUBLIC_API_BASE_URL` | Base URL the app calls, e.g. `http://localhost:8010/api/v1` |
| `apps/mobile/.env` | `EXPO_PUBLIC_GOOGLE_MAPS_API_KEY` | Optional. Set to render the real map view. Needs **Maps JavaScript API** enabled (separately from the backend key's Directions/Places APIs) — without it the map fails with `ApiNotActivatedMapError` in the browser console. This key is unavoidably visible in the client bundle/page source; restrict it by HTTP referrer in Google Cloud Console for anything beyond local dev. |

The backend's `GOOGLE_MAPS_API_KEY` and the mobile app's `EXPO_PUBLIC_GOOGLE_MAPS_API_KEY` can be the same key (reused in this project) or different keys — the backend one only ever runs server-side, while the mobile one is embedded in the page source by necessity, so it has a different risk profile even when the value happens to match.

## Demo scenario reliability

The 4 demo scenarios in `app/seed.py` need to reproduce the same Low/High/Unavailable outcome every time, which two things get in the way of when `GOOGLE_MAPS_API_KEY` is live:

- **Google Directions isn't guaranteed to return the same alternative routes twice.** `CachedSnapshotRoutingProvider` (`routing_adapter.py`) wraps the live provider: `seed.py` saves each demo pair's fetched routes to `demo_route_cache.json` once, and any later request for that exact (origin, destination) replays the cached routes instead of asking Google again. Non-demo pairs pass through live as normal.
- **Real CBD streets seeded for different demo scenarios often overlap** (most routes in the compact grid share a stretch of Swanston St or similar), so a live sensor-match query would otherwise average in another scenario's crowd counts. `route_comparison.py` scopes sensor matching to one scenario's own sensors (`demo-{scenario.key}-*`) whenever the requested pair matches a pinned scenario in `DEMO_SCENARIO_KEY_BY_PAIR`; freeform pairs still match against all active sensors.

Re-run `python -m app.seed` after changing `DEMO_SCENARIOS` and delete `demo_route_cache.json` first so it re-pins fresh routes for the new pairs.

## Known limitations

- Without `GOOGLE_MAPS_API_KEY` set, routing falls back to a fixed two-route demo generator and address search falls back to a 5-place gazetteer.
- Without `EXPO_PUBLIC_GOOGLE_MAPS_API_KEY` (or without Maps JavaScript API enabled on it), the map area shows a "Map failed to load" placeholder instead of crashing the screen.
- Pedestrian data is seeded manually, not ingested from City of Melbourne open data (and expires 30 minutes after seeding — see above).
- Refuge ("quiet place") candidates are seeded manually into the `places` table, not a real search over open data.
- No user accounts, offline maps, turn-by-turn navigation, or next-hour prediction (out of scope for this iteration — see requirements section 4.4).
- "Walk to this refuge" is a terminal UI confirmation, not real walking directions.

See [`CalmPath_App_Development_Requirements.md`](CalmPath_App_Development_Requirements.md) section 20, "Decisions Required Before Development," for what's still open.
