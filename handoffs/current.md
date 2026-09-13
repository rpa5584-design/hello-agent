# RoomTour current handoff

## Current state

Assignment 1 Part 1 hotel-stay search is implemented in the working tree on main. Changes have not been committed or pushed. The project is located at `C:\Users\alana\Desktop\RoomTour`. The visible heading and browser title are RoomTour; the FastAPI title is RoomTour API.

Vue provides a labelled hotel-name input, Search button, and seven-column table. Python reads the supplied hotels.csv (8 hotels) and trips.csv (12 stays), joins on hotel_id, and returns one row per matching trip through `/api/stays?hotel_name=...`. Partial case-insensitive matching, multiple stays, no matches, loading, blank input, and request errors are handled. Existing calculator modules/endpoints remain.

## Verified evidence

The latest Part 1 pre-commit verification confirmed the RoomTour repository location, branch `main`, all six required project documents, and the backend/frontend implementation files, CSVs, and tests. Nothing was staged.

- Backend: 17 tests passed using `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests`; one Starlette/httpx deprecation warning remains.
- Frontend: all 10 tests passed using `node --test tests/*.test.js`.
- Oxlint and ESLint passed without fix/cache flags; `npm run build` passed.
- Frontend tests and build initially hit sandbox `spawn EPERM` errors, then passed when retried with execution permission.
- Git whitespace checks found no errors in tracked changes or untracked text files; only line-ending conversion warnings were reported.
- No source or documentation files were edited during that verification. The build generated ignored output, and Git status remained unchanged. Nothing was committed or pushed.

Earlier live checks confirmed backend health, frontend HTTP access, and Harbor through the frontend proxy returning T001 and T009. The user subsequently reported verifying the RoomTour heading/title, both Harbor stays, all seven table columns, and the completed no-results message. These browser results are user-reported. No fresh live endpoint or browser smoke test, or screenshot-content inspection, was performed during the latest pre-commit verification. See `docs/verification.md` for the earlier evidence and its limits.

Earlier work left servers running at ports 8000 and 5173 at the user's request. Their current state was not checked during pre-commit verification. Check process ownership and runtime state before restarting any service.

## Remaining limitations

- Keyboard behavior, responsive layout, table scrolling, loading/error interactions and recovery, a successful search after no results, browser error logs, and the live FastAPI documentation title remain unverified in the recorded evidence.
- Four screenshots exist in docs: `part1-success.png`, `part1-no-results.png`, `part1-success (2).png`, and `part1-no-results (2).png`. Their contents were not independently inspected. The user explicitly requested keeping all screenshot files as they are; the extra files are no longer a cleanup blocker.
- Listed trips are not live availability; no booking or inventory features exist.
- CSV parsing assumes supplied structure and referential integrity; comprehensive malformed-data handling is outside the implemented scope.
- Existing Starlette/httpx deprecation warning remains; no dependency changes authorized.
- Package metadata, frontend/README.md, and the backend package docstring were excluded from the earlier naming update. The project-folder rename is complete.

## Next task

Review the README and handoff corrections. The requested automated pre-commit checks pass; the browser evidence limits above remain. Preserve all screenshot files, supplied CSVs, and existing uncommitted work. Do not commit or push without user authorization.

## Documentation update

README and this handoff now record the current RoomTour location. This handoff summarizes the latest verified Part 1 state without claiming a fresh browser smoke-test pass.
