# RoomTour

RoomTour Assignment 1 Part 2 is a local Vue 3, FastAPI, and SQLite application for hotel-name search and simulated booking CRUD. Select a demo user, search hotels, book a listed stay, read history, cancel while retaining the record, and delete newly generated test bookings. Instructor bookings are protected from deletion. Legacy calculator endpoints remain for regression coverage.

## Setup and run

Project: `C:\Users\alana\Desktop\RoomTour`. Development branch: `part2-sqlite-crud`.

Existing dependencies are in backend/.venv and frontend/node_modules. On a fresh checkout, create a Python virtual environment, install backend/requirements.txt, and run npm ci in frontend/. Use a Node version supported by frontend/package.json. Part 2 uses built-in sqlite3; no additional dependencies or environment variables are required.

Keep hotels.csv, trips.csv, users.csv, and bookings.csv in backend/data/. From the project root, run in separate PowerShell terminals:

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Open [RoomTour](http://127.0.0.1:5173/). [FastAPI documentation](http://127.0.0.1:8000/docs) is available locally. Vite proxies /api to the backend. Check port ownership before launch; never stop unrelated processes.

## Data and persistence

First initialization creates backend/data/roomtour.sqlite3 and seeds all four CSVs in one transaction: 8 hotels, 12 trips, 6 users, and 6 bookings. Instructor IDs and values are preserved; every application database connection enforces foreign keys.

Later starts reuse the initialized database without reloading or duplicating starter rows, even when a table is empty. Creation, cancellation, and deletion persist after browser refresh and service restart. The database and journals are ignored by Git; CSVs are never rewritten.

Existing uninitialized or unsupported databases cause startup to fail rather than silently reseed. Failed first imports roll back tables and rows but leave an uninitialized file. Inspect and back up an existing database before explicit manual recovery. Never delete/reset the database during normal launch or verification.

Part 1 hotel search still reads hotels.csv and trips.csv directly, joins by hotel_id, and returns one row per listed stay. Matching is case-insensitive and partial, trimming surrounding whitespace. Harbor returns T001 and T009; no matches return an empty stays array. These are listed stays, not live inventory.

## API and structure

| Route | Behavior |
|---|---|
| GET /api/health | Health status |
| GET /api/stays?hotel_name=... | Existing hotel search |
| GET /api/users | Demo users |
| POST /api/bookings | Create confirmed booking from user_id and trip_id; 201 |
| GET /api/bookings?user_id=... | Joined history, including both statuses |
| PATCH /api/bookings/{booking_id} | Accept status cancelled only; retain record |
| DELETE /api/bookings/{booking_id} | Delete generated test booking; 204 |

Missing records return 404, invalid requests 422, and protected deletion 403. New booking IDs use B- plus a UUID.

- backend/app/main.py: startup and router registration.
- backend/app/database.py and seed.py: SQLite schema, connections, and one-time seed.
- backend/app/models.py, controllers/booking_controller.py, and booking_routes.py: models, CRUD, and thin HTTP adapters.
- backend/app/travel.py and travel_routes.py: preserved CSV-based search.
- frontend/src/components/: user selection, results, booking history, and feedback.
- frontend/src/composables/ and api/: interface state and HTTP calls.
- docs/design.md, docs/verification.md, prompts/part2-selected.md, handoffs/current.md: project context.

## Verification

From backend/:

```powershell
.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider tests
```

From frontend/:

```powershell
node --test tests/*.test.js
node node_modules/oxlint/bin/oxlint .
node node_modules/eslint/bin/eslint.js .
npm run build
```

These lint commands avoid source changes; npm run lint auto-fixes. Run git diff --check from the root and also review untracked text files. Latest recorded results: 29 frontend tests, 66 backend tests, lint, production build, and whitespace checks passed. See docs/verification.md for manual evidence and limits.
