# Hike Finder

Natural-language hike search for Switzerland. You type something like
*"a loop hike near Seealpsee, around 10 km, not too much climbing"* — the backend
sends the prompt to the OpenAI API to extract structured filters (location,
distance, elevation, loop, trail/surface type), matches them against the official
Swiss **Wanderland** hiking network (SchweizMobil / ASTRA, via opendata.swiss),
scores the candidates, and returns ranked hikes. The frontend shows result cards
and a Leaflet map with the GPX track, and users can also upload their own hikes.

## Repo layout

```
backend/    FastAPI app + data-enrichment pipeline scripts
frontend/hike-finder/   Create React App SPA (+ Capacitor Android wrapper)
```

Key backend files:

| File | Role |
|---|---|
| `main.py` | FastAPI app: loads data, GPT prompt parsing, filtering/scoring, endpoints `/recommendations`, `/hike`, `/gpx`, `/download/...` |
| `upload.py` | Router for user-contributed hikes (`/upload_hike`, `/preview_gpx`) |
| `models/`, `managers/`, `utils/` | Hike serialization, GPX generation, nearest public-transport stop (GTFS) |
| `sync_data.py` → `enrich_with_wanderweg.py` → `final_enrichment.py` → `canton_enrichment.py` | Data pipeline (see below) |

## Running it

Backend (Python 3.10+):

```bash
cd backend
pip install -r requirements.txt
echo OPENAI_API_KEY=sk-... > .env        # .env is gitignored — create it on every machine
uvicorn main:app --reload                # http://127.0.0.1:8000
```

Run from inside `backend/` — `contributions.csv` and `uploads/` are resolved
relative to the working directory.

Frontend:

```bash
cd frontend/hike-finder
npm install
npm start                                # http://localhost:3000, expects backend on :8000
```

## Data

The app only needs four data files at runtime, all committed:

- `backend/Etappe_final_enriched_with_cantons.gpkg` — hiking **stages** (~40 MB)
- `backend/Route_final_enriched_with_cantons.gpkg` — full **routes** (~40 MB)
- `backend/data/stops.txt` — GTFS public-transport stops (~7 MB)
- `backend/contributions.csv` + `backend/uploads/` — user-contributed hikes

Everything else (the ~1 GB `backend/wanderland_2056.shp/` raw export and all
intermediates) is **gitignored** because it can be re-downloaded/regenerated:

1. Raw Wanderland network: `python sync_data.py` (opendata.swiss CKAN API,
   dataset `langsamverkehr-wanderland-schweiz`) or a SchweizMobil shapefile export.
2. `python enrich_with_wanderweg.py` — spatial join with `WanderWeg.shp` to add
   surface (`BelagTLM`) and path category (`WegKat`).
3. `python final_enrichment.py` — adds nearby lakes / terrain / area / place
   names from **swissTLM3D** layers. ⚠️ Reads the swissTLM3D shapefiles from
   hardcoded `C:\Users\...\Downloads` paths — download them from swisstopo and
   adjust the paths before rerunning.
4. `python canton_enrichment.py` — joins `landesforstinventar-kantone_2056.geojson`
   (committed) to produce the two final `*_with_cantons.gpkg` files.

⚠️ Steps 2–4 still contain hardcoded absolute paths — only needed when
regenerating the data, not for running the app.

## Known quirks (as of Aug 2026)

- The GPT call (`gpt-3.5-turbo`) parses the reply with `json.loads` without JSON
  mode — a chatty reply silently degrades to a no-filter fallback. Upgrading to a
  current model with structured output would help.
- `upload.py` writes 14 CSV values under a 13-column header (`is_loop` misaligned).
- CORS is wide open and `/download/{filename}` doesn't sanitize the filename.
- `frontend/hike-finder/src/config.js` hardcodes a LAN IP for the Android build;
  `SubmitHike.js` hardcodes `localhost:8000` instead of using `getBackendUrl()`.
- Scratch files: `tryout*.py`, `check.py`, `checkgpx.py`, `enriched_viewer.py`.
