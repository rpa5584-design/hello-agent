# RoomTour Part 1 verification

## Automated checks

From `backend/`, run `.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider tests`.
From `frontend/`, run `node --test tests/*.test.js`, `npm run lint`, and `npm run build`.
The lint script uses auto-fix. For a smoke test that must not edit source, use `node node_modules/oxlint/bin/oxlint .` and `node node_modules/eslint/bin/eslint.js .` instead.

## Running application checks

Check ports 8000 and 5173 before starting services using the README commands. Reuse appropriate existing services; never stop unrelated processes. Unless asked to keep services running, stop only services started for the verification run.

1. GET `/api/health`: expect HTTP 200 and `{"status":"ok"}`.
2. GET `/api/stays?hotel_name=Harbor`: expect HTTP 200 and two stays, T001 and T009, for H001 (Harbor Lantern Hotel), with rate 150 USD. Check-in/out pairs are 2026-09-18/2026-09-20 and 2026-10-02/2026-10-04.
3. GET `/api/stays?hotel_name=Nonexistent`: expect `{"stays":[]}`.
4. Missing or whitespace-only `hotel_name`: expect HTTP 422.
5. Repeat the Harbor request through frontend port 5173 to check the proxy.
6. In the browser, confirm RoomTour as heading and browser title, then search Harbor. Confirm the two rows and the seven labels: Hotel name, City, State, Stay name, Check-in, Check-out, Nightly rate (USD).
7. Search Nonexistent; confirm “No matching hotel stays found.” appears only after completion. Search Harbor again and confirm results replace the message.
8. Check loading feedback, disabled controls while pending, a readable request error, and recovery. Use supported browser test facilities if available; do not interrupt unrelated services. Report any untested state.
9. Check keyboard submission/focus, narrow and wide layouts, table scrolling, and browser errors. Confirm the API documentation title is RoomTour API.

## Observed evidence before the naming update

- Backend suite: 17 passed, including six travel cases and eleven calculator regression tests. One existing Starlette/httpx deprecation warning.
- Frontend suite: 10 passed, including five travel tests covering request encoding, multiple results, no-results timing, failures/retry, blank input, and invalid responses.
- Frontend lint and production build passed.
- Live backend health returned ok; frontend returned HTTP 200; a Harbor request through port 5173 returned T001 and T009.

These are recorded checks from the Part 1 implementation in this task, not a claim of a fresh full smoke test. Frontend state tests use mocked requests; backend tests read the supplied CSVs.

## Naming-update checks

Read-only Oxlint and ESLint checks passed, the frontend production build passed, and Git whitespace checks passed after the RoomTour title edits. Application titles were checked in source. No fresh full test suite or browser smoke test was run for this naming/documentation-only change.

## Completed manual RoomTour browser verification

The user reported completing these checks after the RoomTour naming update:

- The page heading and browser title show RoomTour.
- Searching for `Harbor Lantern Hotel` returned 2 matching stays: Boston Harbor Weekend and Boston Autumn Weekend.
- The results table displayed all seven expected columns: Hotel name, City, State, Stay name, Check-in, Check-out, and Nightly rate (USD).
- Searching for `Nonexistent Hotel` displayed “No matching hotel stays found.”

Screenshot evidence files are present: [successful search](part1-success.png) and [no results](part1-no-results.png). The manual results above are user-reported; the screenshots were not independently inspected during this documentation update.

These specific browser checks are complete. Keyboard behavior, responsive layout, table scrolling, loading/error interactions and recovery, a successful search after the no-results state, browser error logs, and the live FastAPI documentation title have not been reported as verified. They remain outstanding; no full browser smoke-test pass is claimed.
