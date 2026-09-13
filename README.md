# RoomTour

RoomTour is the Assignment 1 Part 1 local hotel-stay search application, adapted from the course calculator project. Vue 3 provides the interface, Python reads the supplied CSV files, and FastAPI connects them. Enter a hotel name and select Search to see matching hotels and listed stays in a plain table.

## Current structure

The project is located at `C:\Users\alana\Desktop\RoomTour`.

- `frontend/src/App.vue`: search form and loading, error, and no-match messages.
- `frontend/src/components/HotelStaysTable.vue`: results table.
- `frontend/src/composables/useHotelSearch.js`: search state.
- `frontend/src/api/travel.js`: HTTP access.
- `backend/app/main.py`: FastAPI entry point and router registration.
- `backend/app/travel_routes.py`: stay-search route.
- `backend/app/travel.py`: CSV loading and hotel/trip join.
- `backend/data/`: supplied hotels.csv and trips.csv.
- `backend/tests/`, `frontend/tests/`: travel tests and retained calculator regression tests.
- `docs/design.md`, `docs/verification.md`: design and verification.
- `prompts/part1-selected.md`, `handoffs/current.md`: project context.

Legacy calculator modules and endpoints remain, but the visible interface is RoomTour.

## Local setup and launch

Existing dependencies are in `backend/.venv` and `frontend/node_modules`. No dependencies were added for Part 1. On a fresh checkout, create a Python virtual environment and install `backend/requirements.txt`, and use `npm ci` in `frontend/`. Keep the supplied CSVs in `backend/data/`. No environment variables are required.

Run in separate PowerShell terminals, starting from the project root:

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Open http://127.0.0.1:5173/ . FastAPI documentation is at http://127.0.0.1:8000/docs . Vite proxies `/api` to the backend. Check ports before launching; do not stop unrelated processes.

## Data and API

- `hotels.csv`: `hotel_id,hotel_name,city,state,nightly_rate_usd` (8 hotels).
- `trips.csv`: `trip_id,hotel_id,trip_name,check_in,check_out` (12 stays).

Python reads both files on each search using paths relative to the backend code. Trips join to hotels by `hotel_id`. Each trip produces one row, so a hotel may appear more than once. Trip rows describe listed stays, not live availability or booking inventory.

`GET /api/stays?hotel_name=Harbor` performs a case-insensitive partial hotel-name search, trimming surrounding whitespace. It returns `{"stays": [...]}`. Each record contains `hotel_id`, `hotel_name`, `city`, `state`, `nightly_rate_usd` (number), `trip_id`, `trip_name`, `check_in`, and `check_out`. Dates use `YYYY-MM-DD`. Harbor returns T001 and T009 for Harbor Lantern Hotel.

No matches return HTTP 200 with `{"stays": []}`. Missing or blank hotel names return HTTP 422. The frontend shows Hotel name, City, State, Stay name, Check-in, Check-out, and Nightly rate (USD). It distinguishes loading, failed requests, and completed searches with no matches.

## Verification

From `backend/`:

```powershell
.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider tests
```

From `frontend/`:

```powershell
node --test tests/*.test.js
npm run lint
npm run build
```

The lint script auto-fixes; inspect its diff afterward. See `docs/verification.md` for read-only lint commands, observed results, and outstanding browser checks.
