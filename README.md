# RoomTour

RoomTour is a local Vue 3, FastAPI, and SQLite application. Assignment 2 Part 1 adds live hotel discovery and a map while preserving the existing hotel-name search and simulated booking CRUD. Select a demo user, search hotels, book a listed stay, read history, cancel while retaining the record, and delete newly generated test bookings. Instructor bookings are protected from deletion.

## Assignment 2 Part 1: Live hotel search and map

Enter a five-digit U.S. ZIP code; leading zeros are preserved. The backend resolves the requested U.S. postcode through Geoapify, then retrieves hotels within 5 km of the resolved point. The hotel list and Leaflet map use the same results, with OpenStreetMap tiles and visible attribution. Selecting a hotel in either view selects the same provider place_id in the other; list controls support keyboard selection.

Live hotels display available provider names and addresses without invented prices, ratings, room availability, or booking claims. Results vary, and the interface discloses when the result limit is reached. Invalid ZIPs, unresolved locations, empty results, and service failures have distinct feedback. New searches clear previous results, map markers, and selection. Existing local hotel search and bookings remain separate and unchanged.

## Setup and run

Project: `C:\Users\alana\Desktop\RoomTour`. Current branch: `rag_integration`.

Existing dependencies are in backend/.venv and frontend/node_modules. On a fresh checkout, create a Python virtual environment, install backend/requirements.txt, and run npm ci in frontend/. Use a Node version supported by frontend/package.json. The existing local booking functionality uses built-in sqlite3. Live hotel discovery requires the Geoapify configuration below.

For Geoapify configuration, place `.env` in the project root beside `frontend/` and `backend/`, with the `GEOAPIFY_API_KEY` setting. The API key remains backend-only; never put it in frontend code or a `VITE_` variable. OpenStreetMap tiles require no private frontend credential. Restart the backend after changing `.env`. Existing process environment variables take precedence. `/api/health` reports application status and whether the key is configured; it never returns the key or contacts Geoapify.

For the selected instructor-permitted free Nemotron provider through OpenRouter, `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` are required local backend configuration variables for provider integration. Set them in the same ignored project-root `.env`; `OPENROUTER_MODEL` contains the selected provider model ID, with no hard-coded application default. Never put credentials in frontend code or a `VITE_` variable. Restart the backend after changing configuration; existing process environment variables take precedence. `/api/health` reports only boolean `openrouter_configured` and `openrouter_model_configured` statuses, preserving the existing `status` and `geoapify` fields. It never exposes credentials or contacts either provider. Configuration status does not verify model availability or provider access; successful basic and two-stage calls are recorded in the verification evidence; availability can change. Existing hotel and booking features do not require OpenRouter configuration.

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

Schema version 4 adds only `conversation_history` and its `(conversation_id, message_id)` index, preserving all existing tables and records. Existing versions 1–3 migrate transactionally through the required additive steps; fresh databases receive version 4. Trace columns are `message_id` (integer primary key), `conversation_id`, `timestamp` (UTC), `role`, `content`, and `stage`. Each backend-controlled append commits independently, so completed steps survive a later provider/retrieval failure. Trace connections may insert only history records; model-generated retrieval remains limited to the three approved hotel tables on its separate read-only connection.

`POST /api/rag/answer` optionally accepts a UUID `conversation_id` to reuse a conversation, or creates one. Success and error responses include that ID. Expected stages are `user_question`, `proposed_sql`, `executed_sql`, `retrieval_result`, `assistant_answer`; failures append an `error` without fabricating a successful answer. If history storage is unavailable, the request fails rather than silently proceeding without a trace. `GET /api/rag/conversations/{conversation_id}` returns safe records ordered by `message_id`, up to 100 per page; use `after_message_id` and returned `next_after_message_id` to load more. Unknown IDs return empty messages. Configured credentials and authorization values are redacted before storage and again before returning history. No conversation history is supplied to the model; each RAG question remains independent.

First initialization creates backend/data/roomtour.sqlite3 and seeds all four CSVs in one transaction: 8 hotels, 12 trips, 6 users, and 6 bookings. Instructor IDs and values are preserved; every application database connection enforces foreign keys.

Later starts reuse the initialized database without reloading or duplicating starter rows, even when a table is empty. Creation, cancellation, and deletion persist after browser refresh and service restart. The database and journals are ignored by Git; CSVs are never rewritten.

Assignment 2 Part 2 schema initialization migrates existing version-1 databases to version 2 transactionally, adding empty `saved_hotels` and `demo_hotel_nights` tables. Version 3 then adds `saved_hotel_zips` to store each searched ZIP/location association; version-2 databases migrate directly to version 3. Fresh databases receive the same schema. Repeated startup does not reseed or alter existing records. No additional setup or dependencies are required.

Saved API hotels map `place_id` verbatim to `hotel_id`, `name` to nullable `name`, `formatted_address` to nullable `address`, and `latitude`/`longitude` to required, range-checked coordinates. The provider ID is the primary key. Daily records use `(hotel_id, stay_date)` as their primary key and reference `saved_hotels`; dates must be valid `YYYY-MM-DD` dates. Nonnegative integer defaults of `nightly_rate_cents=10000` ($100.00) and `rooms_available=20` are fictional classroom values, not hotel API data. Saving and removal are available beside ZIP-search hotel results. Saving creates five demo nights for October 10–14, 2026 without overwriting existing nightly values. Removing deletes the hotel, all its ZIP associations, and its demo nights transactionally; instructor records remain separate.

Existing uninitialized or unsupported databases cause startup to fail rather than silently reseed. Failed first imports roll back tables and rows but leave an uninitialized file. Inspect and back up an existing database before explicit manual recovery. Never delete/reset the database during normal launch or verification.

Part 1 hotel search still reads hotels.csv and trips.csv directly, joins by hotel_id, and returns one row per listed stay. Matching is case-insensitive and partial, trimming surrounding whitespace. Harbor returns T001 and T009; no matches return an empty stays array. These are listed stays, not live inventory.

ZIP searches now request local saved hotels first. A successful empty local lookup falls back to the unchanged Part 1 provider endpoint; storage failures show an error and never fall back. Local results are labelled Saved locally and describe a saved subset, not complete area inventory. API results are labelled separately. Saved status is reloaded from SQLite by provider ID on each search, including searches after page refresh. New API hotels are not automatically saved.

## API and structure

The chatbot panel below ZIP search sends hotel questions to `/api/rag/answer`. It retains only the current conversation ID in browser localStorage, restores it on page load, and sends it with subsequent questions, including after a failed request when the backend provides the ID. Each assistant answer has an expandable RAG-details section showing conversation ID, proposed/executed SQL, row count, and bounded rows. Reload saved trace uses the existing history endpoint and displays up to 100 ordered records. Conversation IDs group persisted traces; the model does not yet receive earlier questions, so users must include full ZIP/date context in each question. A page refresh restores the conversation ID without sending a message. Answers/details remain in memory; Reload saved trace retrieves the persisted SQLite history. The basic `/api/chat` endpoint and its API helper remain available, but the hotel-question panel uses RAG.

`POST /api/rag/answer` accepts `{ "question": "..." }` and performs Stage 1, independently revalidated SQLite retrieval, then Stage 2 using only the original question, hotel-assistant instructions, and retrieved records. Responses contain `conversation_id`, `answer`, `proposed_sql`, `executed_sql`, `retrieved_row_count`, and `retrieved_rows`. Retrieval opens the existing RoomTour database in read-only URI mode, enables query-only protection, and authorizes only SELECT/read operations on the three hotel tables and approved functions. Limits are 20 rows, 20 distinct output columns, 64 KB of row JSON, a one-second execution deadline, and one million VM steps (progress checks every 1,000 steps); lock waits are bounded to one second. Hotel retrieval performs no writes; backend-controlled trace writes use a separate connection. A safe deterministic no-match answer replaces unsupported model claims when no rows were retrieved; nonempty answers are prompted to remain grounded but do not have a general factual-verification guarantee. Retrieval failures return safe 503 errors; model failures return 502. The frontend hotel assistant uses this full endpoint.

RAG Stage 1 is backend-only: `POST /api/rag/propose-sql` accepts `{ "question": "..." }`, sends the startup-loaded hotel-assistant system prompt and question to the configured model, and returns `{ "sql": "...", "tables": [...] }` only after independent validation. It does not connect to SQLite or execute SQL. Validation accepts a conservative single SELECT subset over the three local hotel tables, requires a positive literal LIMIT, and caps that LIMIT at 20 rows. Comments, subqueries, CTEs, set operations, OFFSET, unapproved tables/functions, and unsupported syntax are rejected; rejected proposals return 422. This is a safety/structure gate, not a guarantee that the model interpreted the question correctly. This proposal-only endpoint makes no second model request; checked retrieval and Stage 2 belong to `/api/rag/answer`. The frontend uses the full `/api/rag/answer` endpoint.

Backend startup loads the UTF-8 `prompts/hotel-assistant.md` file from the project root into `app.state.hotel_assistant_prompt` for RAG service code, before database initialization. Keep that file present and nonempty; missing/unreadable or empty prompts fail startup with a safe configuration error. Loading the prompt makes no provider or database call and does not change the existing basic chat request behavior.

The original basic chat endpoint remains available: `POST /api/chat` accepts `{ "message": "..." }` and receives `{ "reply": "..." }`. The backend uses existing httpx and environment-selected OpenRouter configuration with a 30-second network timeout and no application retries. Missing configuration returns 503; provider errors or unusable responses return 502 with safe application messages. Messages must contain 1–2000 characters after trimming. Chat uses no SQLite retrieval, SQL generation, booking operations, or persistent conversation history; each message is independent and answers are not grounded in local records. Provider request format follows the [official OpenRouter API reference](https://openrouter.ai/docs/api_reference/overview).

| Route | Behavior |
|---|---|
| GET /api/health | Application health, safe Geoapify status, and boolean openrouter_configured / openrouter_model_configured |
| POST /api/chat | Basic independent chat message; returns assistant reply only |
| POST /api/rag/propose-sql | Stage-1 proposal only; validates without retrieval |
| POST /api/rag/answer | Checked hotel retrieval and grounded answer with persisted trace and conversation_id |
| GET /api/rag/conversations/{conversation_id} | Ordered, paginated conversation trace |
| GET /api/demo/zip-location?zip_code=... | Resolve a five-digit U.S. ZIP; defaults to 16802 when omitted |
| GET /api/demo/hotels?zip_code=... | Resolve the ZIP and return provider hotels within 5 km |
| GET /api/local/hotels?zip_code=... | Saved hotels associated with the searched ZIP, stored location and dated demo nights |
| GET /api/local/hotels/ids | All saved provider IDs for database-backed button status |
| POST /api/local/hotels | Save hotel and searched ZIP/location; repeated saves preserve existing records |
| DELETE /api/local/hotels?hotel_id=... | Remove saved hotel, ZIP associations and demo nights together |
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

These lint commands avoid source changes; npm run lint auto-fixes. Run git diff --check from the root and also review untracked text files. Latest verification (October 8, 2026): 295 backend tests and 68 frontend tests passed; both non-fixing linters, production build, and whitespace checks passed. One existing Starlette/httpx deprecation warning remains. See docs/verification.md for manual evidence and limits.

## Revised Part 2 submission evidence

See [final Part 2 report](report.md), [RAG schema/context and observed SQL](docs/rag-context.md), [labeled fixed JSON sample](docs/rag-fixed-sample.json), and [verification log](docs/verification.md). User-reported completed manual checks include populated/no-match/two-night answers, direct DB comparison, RAG details, Ctrl+R ID restoration and restart/trace persistence; saved traces and dated DB values were also inspected read-only. Keyboard/narrow chatbot review remains pending. Report placeholders are `FINAL_COMMIT_PENDING` and `DEMO_VIDEO_LINK_PENDING`; no final assessed RAG commit or Part 2 demo link is asserted yet.
